import traceback, asyncio, os, flet as ft
from bot import Client, respond, load_image, DATA_DIR
from db import save

prev_ins, prev_notes = '', ''
images = []
chat = ft.ListView(expand=True, auto_scroll=True, padding=10, spacing=50)

opened = True

try:
    client = Client()
except:
    client = None

if not os.path.exists(DATA_DIR / 'latex.properties'):
    with open(DATA_DIR / 'latex.properties', 'w') as f:
        f.write('latex=false')
    latex = False
else:
    with open(DATA_DIR / 'latex.properties') as f:
        latex = f.read().split('=', 1)[1].strip().lower() == 'true'

def settings(page: ft.Page):
    page.clean()
    page.title = 'Pulsar \\ Settings'

    def clean_prev(e):
        if save(DATA_DIR / 'prev.json', {'ins': '', 'notes': ''}):
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text('File not found: prev.json!')
                )
            )
        else:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text('Cleaned prev.json!')
                )
            )

    def clean_shorthands(e):
        if save(DATA_DIR / 'shorthands.json', {}):
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text('File not found: shorthands.json!')
                )
            )
        else:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text('Cleaned shorthands.json!')
                )
            )

    def toggle_latex(e):
        global latex
        latex = e.control.value

        if latex:
            for i in range(len(chat.controls)):
                chat.controls[i].controls[0].content = ft.Markdown(chat.controls[i].controls[0].data, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
        else:
            for i in range(len(chat.controls)):
                chat.controls[i].controls[0].content = ft.Text(chat.controls[i].controls[0].data, selectable=True)

    latex_switch = ft.Switch(label='Enable LaTeX', value=latex, on_change=toggle_latex)

    clean_prev_btn = ft.Button(
        'Clean prev.json', width=200, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
        on_click=clean_prev,
        tooltip='Cleans the prev.json (memory) file',
    )

    clean_shorthands_btn = ft.Button(
        'Clean shorthands.json', width=200, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
        on_click=clean_shorthands,
        tooltip='Cleans the shorthands.json (shortcuts) file',
    )

    key = ft.TextField(label='Enter API key here...', max_lines=1, min_lines=1, password=True, can_reveal_password=True)

    async def go_back(e):
        await main(page)

    async def change(e):
        global client
        if not (len(key.value) < 53 or len(key.value) > 53) or len(key.value) == 0:
            if key.value.strip() != '':
                with open(DATA_DIR / 'api.key', 'w') as f:
                    f.write(key.value)

            with open(DATA_DIR / 'latex.properties', 'w') as f:
                f.write(f'latex={str(latex).lower()}')
            
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text('Settings saved!')
                )
            )
            try:
                client = Client()
            except:
                page.show_dialog(
                    ft.SnackBar(content=ft.Text('No API key found or Invalid key! Add a new valid API key'))
                )

            await go_back(None)
        else:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text('Invalid API key')
                )
            )

    back = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_800,
        icon_size=15,
        width=50,
        height=50,
        padding=0,
        alignment=ft.Alignment.CENTER,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=go_back,
        mouse_cursor=ft.MouseCursor.CLICK,
        tooltip='Go Back'
    )

    save_btn = ft.Button(
        'Save', width=100, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
        on_click=change,
        tooltip='Save the Settings',
    )

    page.add(
        back,
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                latex_switch,
                                clean_prev_btn,
                                clean_shorthands_btn,
                                key,
                                save_btn,
                            ],
                            # tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
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
    global images, chat, opened
    page.clean()
    if opened:
        await page.window.center()
        opened = False
    page.title = 'Pulsar'
    page.window.icon = str(DATA_DIR / 'Logo.ico')
    page.bgcolor = ft.Colors.GREY_900

    text_box = ft.TextField(
        label='Ask anything...',
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
            print(f'[IMAGE ERROR] -> {type(err).__name__}: {repr(err)}')
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
        global latex

        if not text.strip():
            return

        # 1 for user, 0 for bot or computer
        bubble_color = ft.Colors.LIGHT_BLUE if role == 1 else ft.Colors.GREY_700
        border_color = ft.Colors.LIGHT_BLUE_300 if role == 1 else ft.Colors.GREY_300
        align = ft.MainAxisAlignment.END if role == 1 else ft.MainAxisAlignment.START

        if latex:
            content = ft.Markdown(text, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
        else:
            content = ft.Text(text, selectable=True)

        message_bubble = ft.Container(
            content=content,
            data=text,
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
        text_box.value = ''
        add.disabled = True
        add.mouse_cursor = ft.MouseCursor.BASIC
        send.disabled = True
        send.style.mouse_cursor = ft.MouseCursor.BASIC

        image_row.controls.clear()
        page.update()

        AddToChat(user_input, 1)

        thinking = True

        async def think():
            AddToChat(('Thinking...'), 0)
            
            dots = 0
            while thinking:
                AddToChat(('Thinking' + '.' * dots), 0, replace_last=True)

                dots = (dots + 1) % 4
                await asyncio.sleep(0.4) 

        async def run_bot():
            global client
            nonlocal user_input, thinking
            try:
                bot_reply = await asyncio.to_thread(respond, client, user_input, images, prev_ins, prev_notes)
            except Exception as err:
                bot_reply = f'[BOT ERROR] -> {type(err).__name__}: {repr(err)}'
                print(bot_reply)
                traceback.print_exc()

            images.clear()

            thinking = False

            AddToChat(bot_reply, 0, replace_last=True)
            print(bot_reply)
            add.disabled = False
            add.mouse_cursor = ft.MouseCursor.CLICK
            send.disabled = False
            send.style.mouse_cursor = ft.MouseCursor.CLICK
            page.update()

        page.run_task(think)
        page.run_task(run_bot)

    text_box.on_submit = Send

    send = ft.Button(
        'Send', width=100, height=50, bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
        on_click=Send,
        tooltip='Send Message'
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
        tooltip='Add Images'
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
        tooltip='Developer Options / Settings'
    )

    if client is None:
        text_box.disabled = True
        send.disabled = True
        send.style.mouse_cursor = ft.MouseCursor.BASIC
        add.disabled = True
        add.mouse_cursor = ft.MouseCursor.BASIC
        page.show_dialog(
            ft.SnackBar(content=ft.Text('No API key found or Invalid key! Go to Settings to add a new API key'))
        )
        page.update()
    else:
        text_box.disabled = False
        send.disabled = False
        send.style.mouse_cursor = ft.MouseCursor.CLICK
        add.disabled = False
        add.mouse_cursor = ft.MouseCursor.CLICK
        page.update()
    
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
