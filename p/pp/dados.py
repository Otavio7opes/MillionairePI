import pandas as pd

questions = []

df = pd.DataFrame(questions, columns = [])
df.to_excel("questions.xlsx", index=False)

print("perguntas nsiridas com sucesso")