"""
Utilitário para criar/atualizar o usuário lucas diretamente no banco.
Use quando tiver problemas com HASH_LUCAS no .env do Windows.

Uso:
    docker exec qualidade-app-1 python3 app/criar_usuario.py lucas "Lucas Silva" SUA_SENHA
"""
import sys
import sqlite3
import bcrypt
import os

DB_FILE = os.getenv("DB_FILE", "/data/dados_inspecoes.db")

def criar_ou_atualizar(usuario: str, nome: str, senha: str):
    h = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(DB_FILE)
    existente = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
    if existente:
        conn.execute("UPDATE usuarios SET hash_senha=?, nome=?, ativo=1 WHERE usuario=?", (h, nome, usuario))
        print(f"✅ Senha do usuário '{usuario}' atualizada com sucesso.")
    else:
        conn.execute("INSERT INTO usuarios (usuario, nome, hash_senha) VALUES (?,?,?)", (usuario, nome, h))
        print(f"✅ Usuário '{usuario}' criado com sucesso.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python3 app/criar_usuario.py <usuario> <nome> <senha>")
        print('Ex:  python3 app/criar_usuario.py lucas "Lucas Silva" minhasenha123')
        sys.exit(1)
    criar_ou_atualizar(sys.argv[1], sys.argv[2], sys.argv[3])
