# Animal Articles Generator

A Python script that generates informative articles about animal species using the DeepSeek API.

The script reads species from `animals.txt`, generates an article for each species, validates the result, and saves the article together with metadata.

## Features

- Reads animal species from `animals.txt`
- Processes one species per line
- Ignores empty lines and duplicate species
- Generates articles using the DeepSeek API
- Includes habitat, diet, behaviour and interesting facts
- Validates that the article has enough content
- Checks whether the species is mentioned in the generated article
- Retries failed API requests up to three times
- Saves an article and a JSON metadata file for each species
- Skips species that have already been processed
- Shows progress after every 10 processed species
- Supports interactive and non-interactive execution
- Uses logging for successful operations, warnings and errors

## Project Structure

```text
project-folder/
├── animal_articles_generator.py
├── animals.txt
├── requirements.txt
├── README.md
├── .gitignore
└── articles/                  # Created automatically after running
    ├── gray_wolf.txt
    ├── gray_wolf.txt.meta.json
    └── ...
```

## Requirements

- Python 3.10 or newer
- A DeepSeek API key

Install the required packages:

```bash
pip install -r requirements.txt
```

Create a `requirements.txt` file with:

```text
requests
tenacity
```

## API Key Setup

The script uses the `DEEPSEEK_API_KEY` environment variable.

### Windows PowerShell

```powershell
$env:DEEPSEEK_API_KEY="your_deepseek_api_key"
```

### Windows Command Prompt

```cmd
set DEEPSEEK_API_KEY=your_deepseek_api_key
```

Do not place your API key directly in the Python file or upload it to GitHub.

## Input File

The repository includes `animals.txt`. Add one animal species on each line.

Example:

```text
Gray wolf
Common dolphin
African elephant
```

Before running the script, you can add, remove or replace species in this file.

## Usage

Run the script from the project folder:

```bash
python animal_articles_generator.py
```

The script creates an `articles/` folder automatically and saves the generated files there.

## Output Files

For every processed species, the script produces two files:

```text
articles/
├── gray_wolf.txt
└── gray_wolf.txt.meta.json
```

The `.txt` file contains the generated article.

The `.meta.json` file contains:

- Species name
- Generation date and time
- DeepSeek model name
- Prompt used to generate the article

## Batch Processing

The script processes species in batches of 10. After every batch, it asks whether processing should continue.

Example prompt:

```text
Continui cu urmatoarele 10 specii? (da/nu):
```

Press `da`, `d`, `yes`, `y`, or Enter to continue.

## Non-Interactive Mode

To continue automatically without confirmation after each batch, set `NON_INTERACTIVE` before running the script.

### Windows PowerShell

```powershell
$env:NON_INTERACTIVE="true"
python animal_articles_generator.py
```

## Duplicate Prevention

If the script finds a metadata file for an animal in `articles/`, it considers that animal already processed and skips it.

For example, if this file exists:

```text
articles/gray_wolf.txt.meta.json
```

then `Gray wolf` will not be generated again during the next run.

## Configuration

The main settings are located at the beginning of the script:

```python
ANIMALS_FILE = "animals.txt"
ARTICLES_FOLDER = "articles"
BATCH_SIZE = 10
```

You can change `BATCH_SIZE` if you want the script to pause after a different number of species.

## Security

Keep the API key private. The `.gitignore` file should exclude environment files, keys, logs and the generated `articles/` directory.

This project sends prompts to the DeepSeek API, so do not use confidential or personal data in the input file.

## License

This project is intended for educational and portfolio purposes.
