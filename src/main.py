import flet as ft

def main(page: ft.Page):
    page.title = 'Plaii'
    page.add(
        ft.Text('Hello world!')
    )
    page.update()

ft.app(target=main)
