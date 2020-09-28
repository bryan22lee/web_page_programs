# har_parse.py

  - Takes in HTTP Archive (.har) file (captured by [WebPageTest](https://www.webpagetest.org/)) and extracts information from the web page load:
    -  onLoad, byteIndex, objectIndex

## Usage on the command line
  - `python3 har_parse.py <filename>`
    - where `<filename>` should replaced with the path to the HAR Archive file being examined
