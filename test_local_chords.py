filepath = '/Users/marques/Documents/Música/Louvor/Primeira Essencia [Elite] _ Ab _ Felipe Rodrigues _ 69BPM _ 4.4.rpp'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

print("Tracks in local file:")
for line in text.splitlines():
    if "NAME" in line and '"' in line:
        print(line.strip())
