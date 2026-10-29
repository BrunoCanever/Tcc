"""Integra o novo crediário à versão já instalada, sem sobrescrever outras telas.

Execute uma única vez com: python -m scripts.aplicar_atualizacao_crediario
Depois execute INSTALAR_TUDO.bat para atualizar banco e inserir os dados DEMO.
"""
import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def atualizar_arquivo(nome, transformar):
    p = RAIZ / nome
    if not p.exists():
        return f'Atenção: arquivo ausente: {nome}'
    anterior = p.read_text(encoding='utf-8')
    novo = transformar(anterior)
    if novo != anterior:
        p.write_text(novo, encoding='utf-8')
        return f'Atualizado: {nome}'
    return f'Já compatível: {nome}'


def patch_main(t):
    if 'from scripts.atualizar_crediario import' not in t:
        m = re.search(r'^(from scripts\.[^\n]+\n)', t, re.MULTILINE)
        if not m:
            raise RuntimeError('main.py sem importações de migração conhecidas.')
        t = t[:m.end()] + 'from scripts.atualizar_crediario import atualizar_banco as atualizar_banco_crediario\n' + t[m.end():]
    if '        atualizar_banco_crediario()' not in t:
        m = re.search(r'^(\s+)(criado\s*=\s*garantir_admin_inicial\(\)|garantir_admin_inicial\(\))', t, re.MULTILINE)
        if not m:
            raise RuntimeError('Local de inicialização do banco não localizado em main.py.')
        t = t[:m.start()] + m.group(1) + 'atualizar_banco_crediario()\n' + t[m.start():]
    return t


def patch_menu(t):
    antes = t
    t = re.sub(r'(\(\s*["\']Crediário["\']\s*,\s*["\']crediario["\']\s*,\s*TelaCrediario\s*,\s*)\(\s*\)(\s*\))',
               r'\1(self.funcionario,)\2', t)
    if 'TelaCrediario, ()' in t:
        t = t.replace('TelaCrediario, ()', 'TelaCrediario, (self.funcionario,)')
    if t == antes and '(self.funcionario,)' not in t:
        raise RuntimeError('Não encontrei a declaração do crediário no menu; verifique manualmente.')
    return t


def patch_instalador(t):
    if 'from scripts.atualizar_crediario import' not in t:
        m = re.search(r'^(from scripts\.[^\n]+\n)', t, re.MULTILINE)
        if not m:
            raise RuntimeError('Instalador sem imports conhecidos.')
        t = t[:m.end()] + (
            'from scripts.atualizar_crediario import atualizar_banco as atualizar_crediario\n'
            'from scripts.popular_crediario_demo import popular_crediario_demo\n'
        ) + t[m.end():]
    if not re.search(r'^\s+atualizar_crediario\(\)\s*$', t, re.MULTILINE):
        m = re.search(r'^def configurar_dados_demo\(\):\s*\n', t, re.MULTILINE)
        if not m:
            raise RuntimeError('Função configurar_dados_demo não localizada.')
        t = t[:m.end()] + '    atualizar_crediario()\n' + t[m.end():]
    if '    cred_demo = popular_crediario_demo()' not in t:
        m = re.search(r'^(\s+)resultado\s*=\s*popular_dados_demo\(\)\s*\n', t, re.MULTILINE)
        if not m:
            raise RuntimeError('Ponto de inserção de dados demo não localizado.')
        t = t[:m.end()] + (
            '    cred_demo = popular_crediario_demo()\n'
            '    print("Crediário DEMO: " + str(cred_demo))\n'
        ) + t[m.end():]
    return t


def patch_sql(t):
    if 'CREATE TABLE IF NOT EXISTS crediario_recebimento (' in t:
        return t
    fonte = (RAIZ / 'scripts' / 'atualizar_crediario.py').read_text(encoding='utf-8')
    modulo = ast.parse(fonte)
    ddl = next(ast.literal_eval(item.value) for item in modulo.body
               if isinstance(item, ast.Assign) and item.targets[0].id == 'DDL')
    return t.rstrip() + '\n\n-- Recibos de baixa do crediário\n' + ';\n\n'.join(ddl) + ';\n'


def patch_reabertura(t):
    if 'já foi fechado e não pode ser aberto novamente' in t:
        return t.replace('''                raise ValueError(
                    "O Caixa Diário de hoje já foi fechado e não pode ser aberto novamente."
                )''', '''                cursor.execute(
                    """UPDATE caixa_diario SET status='ABERTO',
                           id_funcionario_fechamento=NULL, data_fechamento=NULL,
                           valor_contado=NULL, saldo_esperado_fechamento=NULL,
                           diferenca=NULL, observacao_fechamento=NULL
                       WHERE id_caixa=%s""", (existente['id_caixa'],)
                )
                conexao.commit()
                return existente['id_caixa']''')
    return t


def aplicar():
    patches = [
        ('main.py', patch_main),
        ('telas/menu.py', patch_menu),
        ('scripts/instalar_tudo.py', patch_instalador),
        ('banco/banco.sql', patch_sql),
        ('funcoes/caixa_diario_funcoes.py', patch_reabertura),
    ]
    for nome, patcher in patches:
        print(atualizar_arquivo(nome, patcher))
    print('Integração concluída. Execute INSTALAR_TUDO.bat para preparar o MySQL.')


if __name__ == '__main__':
    aplicar()
