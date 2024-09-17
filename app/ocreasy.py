import easyocr
reader = easyocr.Reader(['ru', 'en'])

result = reader.readtext('../images/ivanov.png')

for (bbox, text, prob) in result:
    print(f'Text: {text}, Probability: {prob}')

