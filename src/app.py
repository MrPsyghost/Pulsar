import traceback, asyncio, flet as ft
from bot import respond, load_image, BASE_DIR

prev_ins, prev_notes = '', ''
images = []

def settings(page: ft.Page):
    page.clean()

    key = ft.TextField(hint_text="Enter key here...", max_lines=1, min_lines=1, password=True, can_reveal_password=True)

    async def change(e):
        with open(BASE_DIR / 'api.key', 'w') as f:
            f.write(key.value)
            await main(page)

    submit = ft.Button(
        "Submit", width=100, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
        on_click=change,
        tooltip="Change API Key",
    )

    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                key,
                                submit,
                            ],
                            tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )

async def main(page: ft.Page):
    global images
    page.clean()
    await page.window.center()
    page.title = "Pulsar"
    page.window.width = 1000
    page.window.height = 600
    page.bgcolor = ft.Colors.GREY_900

    chat = ft.ListView(expand=True, auto_scroll=False, padding=10, spacing=50)

    text_box = ft.TextField(
        label="Ask anything...",
        color=ft.Colors.WHITE,
        expand=True,
        height=50,
        border_color=ft.Colors.WHITE,
        focused_border_color=ft.Colors.WHITE,
        label_style=ft.TextStyle(color=ft.Colors.WHITE),
    )

    image_row = ft.Row(spacing=5)
    file_picker = ft.FilePicker()

    def AddImages(files):
        def RemoveImage(e):
            image_card = e.control.data
            image_row.controls.remove(image_card)
            image_row.update()

        image_row.controls.clear()
        images.clear()

        try:
            for p in files:
                load_image(p[1], images)
        except Exception as err:
            print(f"[IMAGE ERROR] -> {type(err).__name__}: {repr(err)}")
            traceback.print_exc()
        
        for i in range(len(files)):
            image_card = ft.Container(
                width=120,
                padding=5,
                border=ft.Border.all(1, ft.Colors.GREY_700),
                border_radius=8,
                content=ft.Column([
                        ft.Stack([
                            ft.Image(src=images[i][1], width=100, height=100, border_radius=6),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
                                width=30,
                                height=30,
                                right=1,
                                top=2,
                                padding=0,
                                data=None,
                                alignment=ft.Alignment.CENTER,
                                on_click=RemoveImage,
                            ),
                        ],
                        width=100,
                        height=100,
                    ),
                    ft.Text(
                        files[i][0],
                        size=12,
                        color=ft.Colors.WHITE,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    )
                ],
                spacing=5,
            ))
            image_card.content.controls[0].controls[1].data = image_card
            image_row.controls.append(image_card)
        page.update()

    async def PickFiles(e):
        files = [(f.name, f.path) for f in await file_picker.pick_files(
            dialog_title='Select Images',
            allowed_extensions=['png', 'jpg'],
            allow_multiple=True,
        )]
        AddImages(files)

    def AddToChat(text: str, role: int, replace_last: bool=False):
        if not text.strip():
            return

        # 1 for user, 0 for bot or computer
        bubble_color = ft.Colors.LIGHT_BLUE if role == 1 else ft.Colors.GREY
        border_color = ft.Colors.LIGHT_BLUE_300 if role == 1 else ft.Colors.GREY_300
        text_color = ft.Colors.BLACK
        align = ft.MainAxisAlignment.END if role == 1 else ft.MainAxisAlignment.START

        message_bubble = ft.Container(
            content=ft.Text(text, color=text_color),
            padding=ft.Padding(10, 8, 10, 8),
            bgcolor=bubble_color,
            border_radius=10,
            border=ft.Border.all(1, border_color),
            width=(page.width * 0.4) if role == 1 else (page.width * 0.95)
        )

        message_row = ft.Row([message_bubble], alignment=align, spacing=0)

        if role == 1:
            if images:
                message_images_row = ft.Row([ft.Image(i[1], width=75, height=75, border_radius=6) for i in images], spacing=5, alignment=ft.MainAxisAlignment.END)
                message = ft.Column([message_images_row, message_row])
            else:
                message = message_row
        else:
            message = message_row

        if replace_last and chat.controls:
            chat.controls[-1] = message
        else:
            chat.controls.append(message)

        page.update()

    def Send(e):
        global images, prev_ins, prev_notes

        if not text_box.value.strip():
            return

        user_input = text_box.value
        text_box.value = ""
        add.disabled = True
        add.mouse_cursor = ft.MouseCursor.BASIC
        send.disabled = True
        send.style.mouse_cursor = ft.MouseCursor.BASIC

        image_row.controls.clear()
        page.update()

        AddToChat(user_input, 1)

        thinking = True

        async def think():
            AddToChat(("Thinking..."), 0)
            
            dots = 0
            while thinking:
                AddToChat(("Thinking" + "." * dots), 0, replace_last=True)

                dots = (dots + 1) % 4
                await asyncio.sleep(0.4) 

        async def run_bot():
            nonlocal user_input, thinking
            try:
                bot_reply = await asyncio.to_thread(respond, user_input, images, prev_ins, prev_notes)
            except Exception as err:
                bot_reply = f"[BOT ERROR] -> {type(err).__name__}: {repr(err)}"
                print(bot_reply)
                traceback.print_exc()

            images.clear()

            thinking = False

            AddToChat(bot_reply, 0, replace_last=True)
            add.disabled = False
            add.mouse_cursor = ft.MouseCursor.CLICK
            send.disabled = False
            send.style.mouse_cursor = ft.MouseCursor.CLICK

        page.run_task(think)
        page.run_task(run_bot)

    text_box.on_submit = Send

    send = ft.Button(
        "Send", width=100, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
        on_click=Send,
        tooltip="Send Message"
    )

    add = ft.IconButton(
        icon=ft.Icons.ADD,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_800,
        icon_size=15,
        width=50,
        height=50,
        padding=0,
        alignment=ft.Alignment.CENTER,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=PickFiles,
        mouse_cursor=ft.MouseCursor.CLICK,
        tooltip="Add Images"
    )

    change_settings = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_800,
        icon_size=15,
        width=50,
        height=50,
        padding=0,
        alignment=ft.Alignment.CENTER,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: settings(page),
        mouse_cursor=ft.MouseCursor.CLICK,
        tooltip="Settings"
    )

    page.add(
        ft.Column([
            chat,
            ft.Container(ft.Column([
                        image_row,
                        ft.Row([change_settings, text_box, add, send]),
                    ],
                    tight=True
                ),
                padding=10,
            )
        ],
        expand=True
    ))

ft.run(main)
