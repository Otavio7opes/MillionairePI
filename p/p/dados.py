import pandas as pd

#pip install openpyxl
#pip install pandas / nebula pandas extension

questions =[
 ["1 + 1 = ?", "1", "2", "3", "4", 1],
 ["Qual e a capital do Brasil?", "Rio de Janeiro", "Sao Paulo", "Brasilia", "Santos", 3]

]

df = pd.DataFrame(questions, columns = ["Perguntas", "Opcao 1", "Opcao 2", "Opcao 3", "Opcao 4", "Resposta"])
df.to_excel("questions.xlsx", index=False)
