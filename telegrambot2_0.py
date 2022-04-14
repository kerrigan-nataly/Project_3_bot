import telebot
import cv2
import requests
import logging
import time
import psycopg2

bot = telebot.TeleBot("5114326352:AAEK9OXCA88M6N0YXl9gi37XV8nSJ7uzdC8")

screen = "im.png"
url = "rtsp://admin:cnhtkrb@192.168.50.139:554/channel=1&stream=1.sdp?"
text_bot = "Нажмите:" \
           " 'камера', чтобы посмотреть, что сейчас на улице; \n" \
           " 'дисплей', чтобы вывести что-то на дисплей; \n" \
           " 'температура', чтобы посмотреть температуру; \n" \
           " 'влажность', чтобы посмотреть влажность; \n" \
           " 'прожектор_вкл', чтобы включить прожектор; \n" \
           " 'прожектор_выкл', чтобы выключить прожектор; \n" \
           " 'сделать_напоминалку', чтобы сделать оповещалку от бота"

inquiry = "http://192.168.50.143/specificArgs?text="

temp = "http://192.168.50.143/getTemp"
display_temp = "http://192.168.50.143/changeState?set=1"
display_hum = "http://192.168.50.143/changeState?set=2"

light_on = "http://192.168.50.144/changeState?set=1"
light_off = "http://192.168.50.144/changeState?set=0"

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

tconv = lambda x: time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(x))


def create_note(time_m, date, firstname, lastname, username, message):
    try:
        con = psycopg2.connect(
            database="test",
            user="postgres",
            password="postgres",
            host="192.168.50.188",
            port="5432"
        )

        print("Ok")
        cur = con.cursor()
        cur.execute(""" CREATE TABLE IF NOT EXISTS NOTES  
             (TIME TEXT NOT NULL,
             DATE TEXT NOT NULL,
             FIRSTNAME TEXT NOT NULL,
             LASTNAME TEXT NOT NULL,
             USERNAME TEXT NOT NULL,
             MESSAGE TEXT NOT NULL);""")
        con.commit()
        print("Table created successfully")
        cur.execute(f"INSERT INTO NOTES (TIME,DATE,FIRSTNAME,LASTNAME,USERNAME,MESSAGE) "
                    f"VALUES ('{str(time_m)}', '{str(date)}', '{firstname}', '{lastname}', '{username}', '{message}')")
        con.commit()
        cur.execute("SELECT * from NOTES")
        list1 = cur.fetchall()
        for i in list1:
            print(i)
    except Exception:
        pass
    finally:
        con.close()


def screen_update():
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        ret, image = cap.read()
        cv2.imwrite(screen, image)
    cap.release()


# -------------------------------------------------------------

def get_request(request_g, sensor_temp_hum=None):
    try:
        response = requests.get(request_g)
        if sensor_temp_hum == "t":
            json_response = response.json()
            temp_str = json_response["temperature"]
            return temp_str
        elif sensor_temp_hum == "h":
            json_response = response.json()
            humidity = json_response["humidity"]
            return humidity
        return "Готово"
    except Exception:
        return "Проблемы с соединением, попробуйте ещё раз позже"


@bot.message_handler(commands=["start"])
def start(m, res=False):
    menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_1 = telebot.types.KeyboardButton("камера")
    button_2 = telebot.types.KeyboardButton("дисплей")
    button_3 = telebot.types.KeyboardButton("температура")
    button_4 = telebot.types.KeyboardButton("влажность")
    button_5 = telebot.types.KeyboardButton("дисплей_температура")
    button_6 = telebot.types.KeyboardButton("дисплей_влажность")
    button_7 = telebot.types.KeyboardButton("прожектор_вкл")
    button_8 = telebot.types.KeyboardButton("прожектор_выкл")
    button_9 = telebot.types.KeyboardButton("сделать_напоминалку")
    menu.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9)
    bot.send_message(m.chat.id, text=text_bot, reply_markup=menu)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == 'камера':
        screen_update()
        img = open(screen, "rb")
        bot.send_photo(message.chat.id, photo=img)
        img.close()
    elif message.text.strip() == 'дисплей':
        bot.send_message(message.chat.id, text="Введите строчку(только цифры и англиские буквы), "
                                               "перед сообщением поставьте '+'.")
    elif message.text.strip() == 'температура':
        bot.send_message(message.chat.id, text=get_request(temp, "t"))
    elif message.text.strip() == 'влажность':
        bot.send_message(message.chat.id, text=get_request(temp, "h"))
    elif message.text.strip() == 'дисплей_температура':
        bot.send_message(message.chat.id, text=get_request(display_temp))
    elif message.text.strip() == 'дисплей_влажность':
        bot.send_message(message.chat.id, text=get_request(display_hum))
    elif message.text.strip() == 'прожектор_вкл':
        bot.send_message(message.chat.id, text=get_request(light_on))
    elif message.text.strip() == 'прожектор_выкл':
        bot.send_message(message.chat.id, text=get_request(light_off))
    elif message.text.strip() == 'сделать_напоминалку':
        bot.send_message(message.chat.id, text="Чтобы сделать заметку, отправьте строку с символом '!' в начале")
    elif message.text.strip()[0] == "+":
        get_str(message)
    # elif message.text.strip()[0] == "?":

    elif message.text.strip()[0] == "!":
        datta = tconv(message.date).split(" ")
        create_note(datta[0], datta[1], message.chat.first_name, message.chat.last_name, message.chat.username,
                    message.text[1:].strip())
        bot.send_message(message.chat.id, text="Готово")
    else:
        bot.send_message(message.chat.id, text="Я не понимаю")


def match(text, alphabet=None):
    if alphabet is None:
        alphabet = set('abcdefghijklmnopqrstuvwxyz:+')
    return not alphabet.isdisjoint(text.lower())


def get_str(message):
    text_handle_list = message.text.strip()[1:].split()
    text_handle = "+".join(text_handle_list)
    if match(text_handle):
        bot.send_message(message.chat.id, text=get_request(inquiry + text_handle))
    else:
        bot.send_message(message.chat.id, text="Введено неправильно, только цифры и английские буквы!!!")


try:
    bot.infinity_polling()
except Exception:
    pass


# по дате сообщение от человека: такое
