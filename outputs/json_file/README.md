# JSON Output Plugin for Opsbox

## Overview

The JSONFileOutput Plugin writes the results of checks to json files, allowing for easy storage and review of the output data.

*This output plugin can be used by adding `json_out` to your pipeline.*

## Features

- **File Output**: Writes results to json files.
- **Customizable Output Folder**: Allows specifying the folder where the results will be saved.
- **Detailed Logging**: Provides detailed logs of the results.

## Configuration Parameters

| Parameter      | Type    | Description                              | Required | Default       |
|----------------|---------|------------------------------------------|----------|---------------|
| output_folder  | str\|None | The folder to output the results to.     | No       | ./findings/   |