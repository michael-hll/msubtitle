
import google.generativeai as genai
import time
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()  # take environment variables from .env.

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def translateSrt(srtFilePath, language, outPath, model_name, verbose = False, errors = []):
  transCommand = "please translate this sentence to {0}: {1}"
  with open(srtFilePath) as f:
      lines = f.readlines()
      with open(outPath, 'w') as wf:
        lineNo = 0
        for line in tqdm(lines):
          line = line.replace('\n', '')          
          if line.isnumeric():
            lineNo = int(line)
          if not (line.isnumeric() or '-->' in line) and line:       
            lineBackup = line     
            line = __askGemini(transCommand.format(language, line), model_name, verbose)
            if not line:
              errors.append(lineNo)
              line = '[TRANSATION-FAIL]: ' + lineBackup
            if verbose:
              print(line)
          wf.write(line + '\n')
          
def __askGemini(input, model_name, verbose=False):
  response = None
  try:    
    model = genai.GenerativeModel(model_name)  
    response = model.generate_content(input)   
    # sleep 1 seconds inorder not reach the upper limit
    time.sleep(1)
    return response.text
  except Exception as e:
    if verbose:
      print(e, response)
    return ''
    
  
          
 