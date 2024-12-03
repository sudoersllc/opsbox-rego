# TextFileOutput Plugin

## Overview

The TextFileOutput Plugin writes the results of checks to text files, allowing for easy storage and review of the output data.

## Key Features

- **File Output**: Writes results to text files.
- **Customizable Output Folder**: Allows specifying the folder where the results will be saved.
- **Detailed Logging**: Provides detailed logs of the results.

## Configuration Parameters

### Text File Configuration

- **output_folder**: The folder to output the results to (default: `./findings/`).

## Example Configuration

```yaml
output_folder: ./findings/
```