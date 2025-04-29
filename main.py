import os
import logging
import sys
import telebot
from telebot import types
from xkcdpass import xkcd_password
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    logger.error("Токен бота не найден! Проверьте .env файл.")
    sys.exit(1)

class XKCDPasswordGenerator:
    """Генератор паролей в стиле XKCD"""
    DELIMITERS_NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    DELIMITERS_FULL = ["!", "$", "%", "^", "&", "*", "-", "_", "+", "=",
                      ":", "|", "~", "?", "/", ".", ";"] + DELIMITERS_NUMBERS

    def __init__(self, filename: str = "wordlist.txt"):
        try:
            self.wordlist = xkcd_password.generate_wordlist(
                wordfile=filename,
                valid_chars="[a-z]",
                min_length=4,
                max_length=10,
            )
        except Exception as error:
            logger.error("Ошибка загрузки wordlist: %s", error)
            raise

    def generate(self, complexity: str = "normal") -> str:
        """Генерация пароля заданной сложности"""
        try:
            if complexity == "weak":
                return xkcd_password.generate_xkcdpassword(
                    self.wordlist,
                    numwords=2,
                    delimiter=""
                )
            if complexity == "normal":
                return xkcd_password.generate_xkcdpassword(
                    self.wordlist,
                    numwords=3,
                    case="random",
                    random_delimiters=True,
                    valid_delimiters=self.DELIMITERS_NUMBERS
                )
            if complexity == "strong":
                return xkcd_password.generate_xkcdpassword(
                    self.wordlist,
                    numwords=4,
                    case="random",
                    random_delimiters=True,
                    valid_delimiters=self.DELIMITERS_FULL
                )
            return ""
        except Exception as error:
            logger.error("Ошибка генерации пароля: %s", error)
            return "Произошла ошибка при генерации пароля"

class PasswordBot:
    """Telegram бот для генерации паролей"""
    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token)
        try:
            self.generator = XKCDPasswordGenerator()
        except Exception as error:
            logger.error("Не удалось инициализировать генератор паролей: %s", error)
            raise
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        @self.bot.message_handler(commands=['start', 'help'])
        def start_handler(message):
            self.send_welcome(message)

        @self.bot.message_handler(commands=['password', 'generate'])
        def password_handler(message):
            self.send_password_options(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            self.handle_password_generation(call)

    def send_welcome(self, message):
        """Отправка приветственного сообщения"""
        markup = types.InlineKeyboardMarkup()
        btn_generate = types.InlineKeyboardButton(
            "Сгенерировать пароль", 
            callback_data="generate"
        )
        markup.add(btn_generate)

        welcome_text = (
            "🔐 *Генератор XKCD-паролей*\n\n"
            "Я создаю легко запоминающиеся, но надежные пароли.\n\n"
            "*Доступные команды:*\n"
            "/password - Выбрать сложность пароля\n"
            "/help - Показать это сообщение"
        )

        try:
            self.bot.send_message(
                message.chat.id,
                welcome_text,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except Exception as error:
            logger.error("Ошибка отправки приветствия: %s", error)

    def send_password_options(self, message):
        """Отправка вариантов сложности пароля"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_weak = types.InlineKeyboardButton("Слабый", callback_data="weak")
        btn_normal = types.InlineKeyboardButton("Обычный", callback_data="normal")
        btn_strong = types.InlineKeyboardButton("Сложный", callback_data="strong")
        markup.add(btn_weak, btn_normal, btn_strong)

        try:
            self.bot.send_message(
                message.chat.id,
                "🔒 Выберите сложность пароля:",
                reply_markup=markup
            )
        except Exception as error:
            logger.error("Ошибка отправки вариантов пароля: %s", error)

    def handle_password_generation(self, call):
        """Обработка выбора сложности пароля"""
        try:
            complexity = call.data
            if complexity in ["weak", "normal", "strong"]:
                password = self.generator.generate(complexity)
                complexity_name = {
                    "weak": "🔓 Слабый пароль",
                    "normal": "🔐 Обычный пароль",
                    "strong": "🔒 Сложный пароль"
                }[complexity]

                response = (
                    f"{complexity_name}:\n`{password}`\n\n"
                    "Сохраните его в безопасном месте!"
                )
                self.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=response,
                    parse_mode='Markdown'
                )
            if complexity == "generate":
                self.send_password_options(call.message)
        except Exception as error:
            logger.error("Ошибка обработки callback: %s", error)
            self.bot.answer_callback_query(
                call.id,
                "Произошла ошибка при генерации пароля",
                show_alert=True
            )

    def run(self):
        """Запуск бота"""
        logger.info("Бот запущен...")
        try:
            self.bot.polling(none_stop=True, interval=0)
        except Exception as error:
            logger.error("Ошибка в работе бота: %s", error)
            raise

if __name__ == '__main__':
    try:
        bot = PasswordBot(TOKEN)
        bot.run()
    except Exception as error:
        logger.critical("Критическая ошибка: %s", error)
        sys.exit(1)
