# File Structure

Data flow:

```txt
Parser -> Optimizer -> Writer
```

* `retype.py` Entry point
* `retype/data.py` Shared data types
* `retype/optimizer.py` Processes intermediate format (e.g., clean up spacing)
* `retype/parser.py` Parses EPUB file into intermediate format
* `retype/writer.py` Writes output file from intermediate format
* `bs4`, `soupsieve`, `tqdm` are external libraries