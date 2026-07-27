# animal_articles_generator.py (v3 - citire fisier extern, batch 10, fara duplicate)
import os
import time
import logging
import json
import requests
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------- config --------------------
ANIMALS_FILE = "animals.txt"
ARTICLES_FOLDER = "articles"
BATCH_SIZE = 10

# -------------------- citire specii din fisier --------------------
def load_species_from_file(filepath: str) -> List[str]:
    """Citeste speciile dintr-un fisier text, cate una pe linie. Ignora liniile goale si duplicatele."""
    if not os.path.exists(filepath):
        logger.error(f"Fisierul {filepath} nu exista!")
        return []
    seen = set()
    species = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            # Elimina ghilimelele daca exista
            name = name.strip('\"\'\"')
            if name and name not in seen:
                seen.add(name)
                species.append(name)
    return species

# -------------------- verificare duplicat --------------------
def is_already_processed(species_name: str) -> bool:
    """Verifica daca exista deja articol sau metadate pentru aceasta specie."""
    filename = f"{species_name.replace(' ', '_').lower()}.txt"
    meta_path = os.path.join(ARTICLES_FOLDER, filename + ".meta.json")
    return os.path.exists(meta_path)

# -------------------- API call with retry --------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def deepseek_flash_generate(prompt: str) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return "Eroare: cheie API lipsa"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Eroare API: {e}")
        raise

# -------------------- validation --------------------
def validate_article(content: str, species_name: str) -> bool:
    if not content or len(content) < 100:
        logger.warning(f"Articol prea scurt pentru {species_name}")
        return False
    # Verificam doar primul cuvant (ex: "lup" din "Lup cenusiu")
    first_word = species_name.split()[0].lower()
    if first_word not in content.lower():
        logger.warning(f"Articolul nu mentioneaza specia {species_name} (cautat: '{first_word}')")
        return False
    return True

# -------------------- generation --------------------
def generate_article(species_name: str) -> str:
    prompt = f"Scrie un articol informativ despre specia {species_name}, incluzand habitat, alimentatie, comportament si curiozitati. IMPORTANT: Trebuie sa scrii numele exact al speciei ('{species_name}') in primele doua propozitii."
    article = deepseek_flash_generate(prompt)
    if not validate_article(article, species_name):
        return None
    return article

# -------------------- saving --------------------
def save_article(species_name: str, content: str, folder: str = ARTICLES_FOLDER, prompt: str = ""):
    os.makedirs(folder, exist_ok=True)
    filename = f"{species_name.replace(' ', '_').lower()}.txt"
    path = os.path.join(folder, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        metadata = {
            "species": species_name,
            "generated_at": datetime.now().isoformat(),
            "model": "deepseek-v4-flash",
            "prompt": prompt
        }
        meta_path = path + ".meta.json"
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(metadata, mf, ensure_ascii=False, indent=2)
        logger.info(f"Articol salvat: {path}")
        return True
    except Exception as e:
        logger.error(f"Eroare la salvarea fisierului {path}: {e}")
        return False

# -------------------- procesare individuala --------------------
def process_species(species_name: str) -> bool:
    """Proceseaza o specie: genereaza si salveaza articolul. Returneaza True daca succes."""
    try:
        article = generate_article(species_name)
        if article is None:
            logger.error(f"Generare esuata pentru {species_name} – articol invalid")
            return False
        prompt = f"Scrie un articol informativ despre specia {species_name}, incluzand habitat, alimentatie, comportament si curiozitati. IMPORTANT: Trebuie sa scrii numele exact al speciei ('{species_name}') in primele doua propozitii."
        return save_article(species_name, article, prompt=prompt)
    except Exception as e:
        logger.exception(f"Eroare neasteptata la procesarea speciei {species_name}: {e}")
        return False

# -------------------- main cu batch si intrebare --------------------
def main():
    all_species = load_species_from_file(ANIMALS_FILE)
    if not all_species:
        logger.error("Nicio specie de procesat. Verifica fisierul animals.txt")
        return
    
    logger.info(f"Specii incarcate din fisier: {len(all_species)}")
    logger.info(f"Lista: {all_species}")
    
    # Filtram doar speciile neprocesate
    to_process = [s for s in all_species if not is_already_processed(s)]
    skipped = len(all_species) - len(to_process)
    if skipped:
        logger.info(f"Sar peste {skipped} specii deja procesate.")
    
    if not to_process:
        logger.info("Toate speciile au fost deja procesate. Nimic de facut.")
        return
    
    logger.info(f"De procesat: {len(to_process)} specii noi.")
    
    success_count = 0
    fail_count = 0
    
    # Verificam daca suntem in mod non-interactiv
    non_interactive = os.getenv("NON_INTERACTIVE", "").lower() in ("1", "true", "yes")
    
    for idx, species in enumerate(to_process, 1):
        logger.info(f"\n--- Procesez {idx}/{len(to_process)}: {species} ---")
        
        success = process_species(species)
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        # Dupa fiecare BATCH_SIZE (sau la final), intreaba daca sa continue
        if idx % BATCH_SIZE == 0 or idx == len(to_process):
            print(f"\n=== Progres: {idx}/{len(to_process)} procesate. Reusite: {success_count}, Esuate: {fail_count} ===")
            if idx < len(to_process):
                if non_interactive:
                    logger.info("Mod non-interactiv: continui automat...")
                else:
                    try:
                        raspuns = input("\nContinui cu urmatoarele 10 specii? (da/nu): ").strip().lower()
                        if raspuns not in ("da", "d", "y", "yes", ""):
                            logger.info("Am oprit procesul la cererea utilizatorului.")
                            break
                    except (EOFError, OSError):
                        # Mediu non-interactiv, continuam automat
                        logger.info("Mediu non-interactiv detectat, continui automat...")
    
    logger.info(f"\n=== Proces terminat ===")
    logger.info(f"Total procesate: {idx}, Reusite: {success_count}, Esuate: {fail_count}")

if __name__ == "__main__":
    main()