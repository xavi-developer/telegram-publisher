import os
import sys
import time
import shutil
import threading
import asyncio
import random
import argparse
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QListWidget, QLineEdit, QCheckBox, QSpinBox, QListWidgetItem, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
from telegram import Bot

MEDIA_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov")

class TelegramPublisher(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.bot = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.running = False
        self.timer = None
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.next_publish_time = 0
        self.published_count = 0
        self.setWindowIcon(QIcon("icon.png"))


    def init_ui(self):
        self.setWindowTitle("Telegram Publisher")
        layout = QHBoxLayout()

        # Left section
        left_layout = QVBoxLayout()
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.select_folder)
        self.folder_label = QLabel("No folder selected")
        self.folder_stats = QLabel("")
        self.subfolder_list = QListWidget()
        left_layout.addWidget(self.folder_button)
        left_layout.addWidget(self.folder_label)
        left_layout.addWidget(self.folder_stats)
        left_layout.addWidget(self.subfolder_list)

        # Right section
        right_layout = QVBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Bot Token")
        self.token_input.setText("123456:AA11BB22")

        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Group ID (-100XXX)")
        self.channel_input.setText("-100XXX")

        self.period_input = QSpinBox()
        self.period_input.setRange(1, 100000)
        self.period_input.setValue(3600)
        self.period_input.setSuffix(" sec")

        self.count_input = QSpinBox()
        self.count_input.setRange(1, 100)
        self.count_input.setValue(1)

        self.publish_button = QPushButton("Publish")
        self.publish_button.clicked.connect(self.start_publishing)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_publishing)
        self.stop_button.setEnabled(False)
        self.countdown_label = QLabel("")

        self.status_label = QLabel("")

        right_layout.addWidget(QLabel("Bot Token:"))
        right_layout.addWidget(self.token_input)
        right_layout.addWidget(QLabel("Group ID:"))
        right_layout.addWidget(self.channel_input)
        right_layout.addWidget(QLabel("Periodicity:"))
        right_layout.addWidget(self.period_input)
        right_layout.addWidget(QLabel("Items per batch:"))
        right_layout.addWidget(self.count_input)
        right_layout.addWidget(self.publish_button)
        right_layout.addWidget(self.stop_button)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.countdown_label)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.load_subfolders()

    def load_subfolders(self):
        self.subfolder_list.clear()
        subfolders = []
        media_count = 0
        has_subfolders = False

        for name in os.listdir(self.folder_path):
            full_path = os.path.join(self.folder_path, name)
            if os.path.isdir(full_path) and name.lower() != "published":
                has_subfolders = True
                if not name.lower().startswith("published"):
                    subfolders.append(name)
                    for root, _, files in os.walk(full_path):
                        if "published" in root:
                            continue
                        media_count += sum(f.lower().endswith(MEDIA_EXTENSIONS) for f in files)

        if has_subfolders:
            for folder_name in subfolders:
                item = QListWidgetItem(folder_name.split(" ", 1)[1])
                item.setData(Qt.UserRole, folder_name)
                item.setCheckState(Qt.Checked)
                self.subfolder_list.addItem(item)
            self.using_subfolders = True
            self.folder_stats.setText(f"Subfolders: {len(subfolders)} | Media files: {media_count}")
        else:
            # No subfolders – show file count in root
            file_list = [f for f in os.listdir(self.folder_path)
                        if f.lower().endswith(MEDIA_EXTENSIONS)
                        and os.path.isfile(os.path.join(self.folder_path, f))]
            media_count = len(file_list)

            item = QListWidgetItem(f"{media_count} media files in main folder")
            item.setData(Qt.UserRole, "")  # No subfolder path
            item.setCheckState(Qt.Checked)
            self.subfolder_list.addItem(item)

            self.using_subfolders = False
            self.folder_stats.setText(f"Media files: {media_count}")

    def start_publishing(self):
        token = self.token_input.text()
        self.bot = Bot(token=token)
        self.running = True
        self.published_count = 0
        self.stop_button.setEnabled(True)
        self.publish_button.setEnabled(False)

        selected_subs = [self.subfolder_list.item(i).data(Qt.UserRole)
                        for i in range(self.subfolder_list.count())
                        if self.subfolder_list.item(i).checkState() == Qt.Checked]

        channel = self.channel_input.text()
        count = self.count_input.value()
        period = self.period_input.value()

        def run_schedule():
            while self.running:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.ensure_future(
                        self.publish_media(selected_subs, channel, count)
                    )
                )
                self.remaining_seconds = period
                QTimer.singleShot(0, lambda: self.countdown_timer.start(1000))
                self.next_publish_time = time.time() + period

                for _ in range(period):
                    if not self.running:
                        break
                    time.sleep(1)

        threading.Thread(target=run_schedule, daemon=True).start()

    def stop_publishing(self):
        self.running = False
        self.publish_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Publishing stopped.")
        self.countdown_timer.stop()

    async def publish_media(self, selected_subs, channel, count):
        all_files = []

        if self.using_subfolders:
            for folder_name in selected_subs:
                thread_id_str, _ = folder_name.split(" ", 1)
                thread_id = int(thread_id_str)
                full_path = os.path.join(self.folder_path, folder_name)
                for fname in os.listdir(full_path):
                    if fname.lower().endswith(MEDIA_EXTENSIONS):
                        fpath = os.path.join(full_path, fname)
                        all_files.append((fpath, thread_id))
        else:
            # Use files from main folder, no thread ID
            for fname in os.listdir(self.folder_path):
                if fname.lower().endswith(MEDIA_EXTENSIONS):
                    fpath = os.path.join(self.folder_path, fname)
                    all_files.append((fpath, None))

        random.shuffle(all_files)
        to_publish = all_files[:count]
    
        for filepath, thread_id in to_publish:
            try:
                send_args = dict(chat_id=channel)
                if thread_id is not None:
                    send_args["message_thread_id"] = thread_id

                if filepath.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    with open(filepath, "rb") as photo:
                        await self.bot.send_photo(photo=photo, **send_args)
                else:
                    with open(filepath, "rb") as video:
                        await self.bot.send_video(video=video, **send_args)

                self.move_to_published(filepath)
                self.published_count += 1
                self.status_label.setText(f"Published: {self.published_count}")
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Failed to publish {filepath}: {e}")

    def update_countdown(self):
        if self.remaining_seconds <= 0:
            self.countdown_label.setText("Publishing...")
            self.countdown_timer.stop()
        else:
            hrs, rem = divmod(self.remaining_seconds, 3600)
            mins, secs = divmod(rem, 60)
            self.countdown_label.setText(f"Next in: {hrs:02}:{mins:02}:{secs:02}")
            self.remaining_seconds -= 1

    def move_to_published(self, filepath):
        dir_path = os.path.dirname(filepath)
        published_dir = os.path.join(dir_path, "published")
        os.makedirs(published_dir, exist_ok=True)
        shutil.move(filepath, os.path.join(published_dir, os.path.basename(filepath)))


def run_cli_mode(bot_token, channel_id, media_folder, items_per_batch):
    from telegram import Bot
    import asyncio

    async def publish():
        bot = Bot(token=bot_token)
        media_files = []

        has_subfolders = any(
            os.path.isdir(os.path.join(media_folder, entry))
            for entry in os.listdir(media_folder)
        )

        if has_subfolders:
            for subfolder in os.listdir(media_folder):
                subfolder_path = os.path.join(media_folder, subfolder)
                if not os.path.isdir(subfolder_path):
                    continue
                if subfolder.lower() == "published":
                    continue
                if " " not in subfolder:
                    print(f"Skipping subfolder '{subfolder}': no thread ID found.")
                    continue

                thread_id_part = subfolder.split(" ", 1)[0]
                if not thread_id_part.isdigit():
                    print(f"Skipping subfolder '{subfolder}': invalid thread ID.")
                    continue

                message_thread_id = int(thread_id_part)

                for fname in os.listdir(subfolder_path):
                    if fname.lower().endswith(MEDIA_EXTENSIONS):
                        media_files.append({
                            "path": os.path.join(subfolder_path, fname),
                            "thread_id": message_thread_id,
                            "subfolder": subfolder_path,
                        })
        else:
            for fname in os.listdir(media_folder):
                if fname.lower().endswith(MEDIA_EXTENSIONS):
                    media_files.append({
                        "path": os.path.join(media_folder, fname),
                        "thread_id": None,
                        "subfolder": media_folder,
                    })

        random.shuffle(media_files)
        to_publish = media_files[:items_per_batch]

        for item in to_publish:
            filepath = item["path"]
            thread_id = item["thread_id"]
            subfolder = item["subfolder"]

            try:
                send_args = dict(chat_id=channel_id)
                if thread_id is not None:
                    send_args["message_thread_id"] = thread_id

                if filepath.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    with open(filepath, "rb") as photo:
                        await bot.send_photo(photo=photo, **send_args)
                else:
                    with open(filepath, "rb") as video:
                        await bot.send_video(video=video, **send_args)

                # Move to "published"
                published_dir = os.path.join(subfolder, "published")
                os.makedirs(published_dir, exist_ok=True)
                shutil.move(filepath, os.path.join(published_dir, os.path.basename(filepath)))

                print(f"Published: {filepath} (Thread ID: {thread_id})")

            except Exception as e:
                print(f"Failed to publish {filepath}: {e}")

    asyncio.run(publish())


def run_cli_mode_wrapper():
    parser = argparse.ArgumentParser(
        description="Telegram Media Publisher CLI/GUI hybrid tool"
    )

    parser.add_argument("--bot", help="Telegram bot token", required=False)
    parser.add_argument("--channel", help="Telegram channel or group ID", required=False)
    parser.add_argument("--folder", help="Path to media folder", required=False)
    parser.add_argument("--items", help="Number of items to publish", type=int, required=False)

    # If no arguments: Launch GUI
    if len(sys.argv) == 1:
        app = QApplication(sys.argv)
        window = TelegramPublisher()
        window.show()
        sys.exit(app.exec())

    # Parse args
    args, unknown = parser.parse_known_args()

    # Show help if:
    #  - Any unknown argument
    #  - Any required argument missing
    if unknown or not (args.bot and args.channel and args.folder and args.items):
        parser.print_help()
        sys.exit(1)

    # Run CLI mode
    run_cli_mode(
        bot_token=args.bot,
        channel_id=args.channel,
        media_folder=args.folder,
        items_per_batch=args.items
    )


if __name__ == "__main__":
    run_cli_mode_wrapper()
