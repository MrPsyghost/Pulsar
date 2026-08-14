import threading, flet as ft
from bot import respond, image

prev_ins, prev_notes = '', ''
images = []

def main(page: ft.Page):
    page.window.center()
    page.title = "Pulsar"
    page.window.width = 1000
    page.window.height = 600
    page.bgcolor = ft.Colors.GREY_900
    
    chat = ft.ListView(expand=True, auto_scroll=True, padding=10)

    text_box = ft.TextField(
        label="Ask me anything", 
        color=ft.Colors.WHITE,
        expand=True, 
        height=50, 
        border_color=ft.Colors.WHITE,
        focused_border_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE)
    )

    image_row = ft.Row([], spacing=5)

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def AddToChat(text: str, role="user", replace_last=False):
        if not text.strip():
            return

        bubble_color = ft.Colors.GREY_500 if role=="user" else ft.Colors.GREY_200
        text_color = ft.Colors.BLACK
        align = ft.MainAxisAlignment.END if role=="user" else ft.MainAxisAlignment.START

        message_bubble = ft.Container(
            content=ft.Text(text, color=text_color),
            padding=ft.Padding(10,8,10,8),
            bgcolor=bubble_color,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_400),
            alignment=ft.alignment.center_left if role=="bot" else ft.alignment.center_right,
            width=page.width * 0.6
        )

        message_row = ft.Row([message_bubble], alignment=align, spacing=0)

        if replace_last and chat.controls:
            chat.controls[-1] = message_row
        else:
            chat.controls.append(message_row)

        page.update()

    def AddImage(e: ft.FilePickerResultEvent):
        if e.files:
            try:
                image(e.files[0].path, images)
            except Exception as err:
                print("Image add error:", err)
                return
            image_row.controls.clear()
            image_row.controls.extend([ft.Image(src=i[1], width=100, height=100) for i in images])
            page.update()

    file_picker.on_result = AddImage

    def Send(e):
        global images, prev_ins, prev_notes

        if not text_box.value.strip():
            return

        user_input = text_box.value
        text_box.value = ""
        add.disabled = True
        send.disabled = True

        image_row.controls.clear()
        page.update()

        AddToChat(user_input, "user")
        AddToChat("Thinking....", "bot")

        def run_bot():
            nonlocal user_input
            try:
                bot_reply = respond(user_input, images, prev_ins, prev_notes)
            except Exception as err:
                bot_reply = f"Error: {err}"

            images.clear()
            image_row.controls.clear()

            AddToChat(bot_reply, "bot", replace_last=True)
            add.disabled = False
            send.disabled = False
            page.update()

        threading.Thread(target=run_bot, daemon=True).start()

    send = ft.ElevatedButton(
        "Send", width=100, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=Send
    )

    add = ft.ElevatedButton(
        "+", width=100, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: file_picker.pick_files(
            dialog_title="Select Image",
            allowed_extensions=["jpg"],
            allow_multiple=False
        )
    )

    page.add(
        ft.Column(
            [
                chat,
                ft.Container(
                    content=ft.Column(
                        [
                            image_row,
                            ft.Row([text_box, add, send], spacing=10)
                        ],
                        tight=True
                    ),
                    padding=10
                )
            ],
            expand=True
        )
    )

    text_box.on_submit = Send

ft.run(main)
