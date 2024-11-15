import flet as ft
import requests
import os
import sys
import shutil
import tempfile

def check_update():
    repo = "ocerqueira/meu-app"
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            latest_release = response.json()
            print(f"Latest release response: {latest_release}")
            latest_version = latest_release.get("tag_name", "Desconhecido")
            assets = latest_release.get("assets", [])

            # Verifica se há um arquivo binário para download
            if assets:
                asset_url = assets[0].get("browser_download_url", "#")
                return latest_version, asset_url
            else:
                return "Erro", "Nenhum arquivo de atualização encontrado"
        elif response.status_code == 404:
            return "Erro", "Repositório ou release não encontrado."
        elif response.status_code == 403:
            return "Erro", "Limite de requisições atingido. Tente novamente mais tarde."
        else:
            return "Erro", f"Erro ao buscar versão: {response.status_code}"
    except Exception as e:
        return "Erro", str(e)

def download_and_replace_executable(download_url):
    try:
        # Cria um arquivo temporário para baixar o executável
        with requests.get(download_url, stream=True) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)

        # Define o caminho do executável atual
        current_executable = sys.executable
        print(f"Current executable path: {current_executable}")

        # Cria backup antes de substituir
        backup_path = current_executable + ".bak"
        shutil.copy(current_executable, backup_path)

        # Move o arquivo baixado para substituir o executável atual
        shutil.move(tmp_file.name, current_executable)

        # Ajusta as permissões do arquivo
        os.chmod(current_executable, 0o755)

        return True
    except Exception as e:
        return str(e)

def main(page: ft.Page):
    page.title = "Atualização de App"

    current_version = "1.0.0"  # Versão atual do aplicativo

    def update_check(e):
        btn_check.disabled = True
        loading_spinner.visible = True
        page.update()

        latest_version, download_url = check_update()

        if latest_version == "Erro":
            status_text.value = f"Erro: {download_url}"
        elif latest_version != current_version:
            status_text.value = f"Nova versão disponível: {latest_version}\nBaixando a atualização..."
            page.update()

            # Baixa e substitui o executável
            update_result = download_and_replace_executable(download_url)

            if update_result is True:
                status_text.value = "Atualização concluída! Reinicie o aplicativo."
            else:
                status_text.value = f"Erro ao atualizar: {update_result}"
        else:
            status_text.value = "Você já está na última versão!"

        btn_check.disabled = False
        loading_spinner.visible = False
        page.update()

    status_text = ft.Text(value="Clique abaixo para verificar atualizações.")
    btn_check = ft.ElevatedButton("Verificar Atualizações", on_click=update_check)
    loading_spinner = ft.ProgressRing(visible=False)

    page.add(
        ft.Column([
            status_text,
            btn_check,
            loading_spinner,
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

if __name__ == "__main__":
    ft.app(target=main)
