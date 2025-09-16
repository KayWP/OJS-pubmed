# PubMed XML Processor

A Python script that processes journal article XML files from Open Journal Systems (OJS) and transforms them into PubMed-compliant XML format for submission to the PubMed database.

## Features

- **Batch Processing**: Processes multiple XML files from an input directory
- **Title Translation**: Retrieves English titles from OJS API using Dutch vernacular titles
- **Abstract Enhancement**: Fetches English abstracts and reorganizes multilingual abstracts
- **Keyword Extraction**: Extracts DC.Subject metadata as keywords
- **XML Restructuring**: Reorganizes XML elements to comply with PubMed DTD requirements
- **Language Standardization**: Converts language codes (e.g., 'dut' to 'NL')
- **Metadata Enrichment**: Adds publication types, article IDs, and other required elements

## Requirements

### Dependencies

```bash
pip install beautifulsoup4 requests pandas python-dotenv lxml
```

### Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
api_key=your_ojs_api_key
journal_title=your_journal_name
journal_abbreviation=Journal_Abbreviation
pubmed_user=your_pubmed_username
pubmed_pass=your_pubmed_password
```

## Directory Structure

```
project/
├── input/              # Place XML files to be processed here
├── output/             # Output directory (created automatically)
├── articleset.xml      # Final combined output file
├── json.txt           # API response cache file
├── .env               # Environment variables
├── main.py            # Main script
└── README.md          # This file
```

## Usage

### Basic Usage

1. Place your XML files in the `input/` directory
2. Run the script:

```bash
python main.py
```

3. The processed XML will be saved as `articleset.xml`

### Advanced Usage

You can also use individual functions programmatically:

```python
from main import rewrite_xml, read_xml_file

# Process a single XML file
xml_content = read_xml_file('path/to/file.xml')
processed_xml = rewrite_xml(xml_content, 'journal_name', 'api_key')
```

## Key Functions

### Core Processing Functions

- `rewrite_xml()`: Main function that orchestrates the entire transformation process
- `process_all_xml_files()`: Batch processes multiple XML files and combines them
- `reorganize_article_xml()`: Reorders XML elements according to PubMed DTD requirements

### Data Retrieval Functions

- `retrieve_json_info()`: Fetches article information from OJS API
- `get_english_abstract()`: Extracts English abstracts from article pages
- `get_dc_subjects()`: Retrieves keyword metadata from article pages

### XML Manipulation Functions

- `add_article_title()`: Adds English article titles
- `replace_vernacular_title()`: Updates vernacular titles with subtitles
- `refurbish_abstracts()`: Reorganizes abstracts by language
- `insert_keywords_after_abstract()`: Adds keyword metadata
- `add_article_id_list()`: Adds DOI information
- `add_publication_type()`: Adds publication type metadata
- `replace_language_tag()`: Standardizes language codes

## XML Transformation Process

The script performs the following transformations:

1. **Title Processing**: Retrieves English titles from OJS API
2. **Abstract Enhancement**: Fetches English abstracts and creates multilingual structure
3. **Metadata Addition**: Adds keywords, publication types, and article IDs
4. **Language Standardization**: Updates language codes for PubMed compatibility
5. **Structure Reorganization**: Reorders elements according to PubMed DTD
6. **DOCTYPE Addition**: Adds proper DOCTYPE declaration for PubMed submission

## Output Format

The script generates a combined `articleset.xml` file containing all processed articles with:

- PubMed-compliant DOCTYPE declaration
- Properly ordered XML elements
- English and vernacular titles
- Multilingual abstracts
- Keyword metadata
- Publication type information
- DOI identifiers

## Error Handling

The script includes error handling for:

- Network connectivity issues
- API response errors
- XML parsing errors
- Missing metadata
- File I/O operations

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Verify your API key and journal title in `.env`
2. **XML Parsing Errors**: Check that input XML files are well-formed
3. **Missing Abstracts**: Some articles may not have English abstracts available
4. **Network Timeouts**: Retry processing if network issues occur

### Debugging

The script outputs detailed information during processing:
- API responses are cached in `json.txt`
- Progress messages are printed to console
- Error messages indicate specific issues

## Configuration

### Journal Settings

Update the `.env` file with your specific journal information:
- `journal_title`: The OJS journal identifier
- `journal_abbreviation`: PubMed-approved journal abbreviation

### Processing Options

Modify the `element_order` list in `reorganize_article_xml()` to change element ordering if needed.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the error messages in the console output
- Verify your `.env` configuration
- Ensure input XML files are properly formatted
