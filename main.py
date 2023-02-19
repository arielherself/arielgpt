import time
import random
import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot
from revChatGPT.V1 import Chatbot
import local_secrets

COOLDOWN: float = 2.0
AN = "This is often caused by:\n  1. Requesting too frequently;\n  2. Too many repeated questions;\n  3. ChatGPT is at \
capacity right now.\n\nTo resolve this, you should first visit chat.openai.com and \
check if there's a bulletin about service outage. If not so, you can wait for about 1 hour \
or use /gpt command to randomly switch to another OpenAI account in the pool.\nSometimes, /reset command also helps."
VOID_HINT = "*ChatGPT didn't respond to your query.* \n" + AN
ERROR_HINT = '*ChatGPT returned an error to your query.*\n' + AN
TIPS = ('Sometimes Telegram marks the rolling text as a flood attack. Please be patient if the output is stuck at some point.', 
        'Ariel GPT Plus gives you the ChatGPT Plus experience on Telegram. Subscribe to it now!', 
        "If the bot doesn't respond to your message, you can reply to one of its messages.", 
        "This bot has a mature exception-processing system. All you need is to wait until it gives you a satisfying response.", 
        'Ariel GPT 2 supports account load-balance. There are multiple OpenAI accounts working for you.', 
        'Regenerate response or repeat your question frequently can cause OpenAI to halt your requests for an hour.',
        '/reset command helps you to start a new conversation.',
        'When using /gpt before your prompt, Ariel GPT randomly choose an OpenAI account to use. If you reply to an answer, it will continue using the current account.')

chatgpt = [Chatbot(config=info) for info in local_secrets.OPENAI_LOGIN_INFO]
chatgpt_plus = [Chatbot(config=info) for info in local_secrets.PLUS_LOGIN_INFO]
bot = AsyncTeleBot(local_secrets.BOT_TOKEN)
current_gpt = random.choice(chatgpt)

class Spinner:
    def __init__(self):
        self._current = '|'
    @property
    def spin(self):
        if self._current == '|':
            self._current = '/'
        elif self._current == '/':
            self._current = '-'
        elif self._current == '-':
            self._current = '\\'
        elif self._current == '\\':
            self._current = '|'
        return self._current

print('Started.')

# prompt = "Hello!"
# response = ''
# 
# for data in chatbot.ask(prompt):
#     response = data['message']
#     print(response)

oc = False
forceStopFlag = False
spinner = Spinner()

def plusAccess(userid: any):
    with open('subscriber.txt') as f:
        user_list = [l.strip() for l in f.readlines() if l.strip() != '']
    return str(userid) in user_list

def op(msg: str):
    n = msg
    try:
        n = n.replace('$$', '`')
    except Exception as e:
        print(f'Error: {e}')
    return n

def stopMarkup() -> telebot.types.InlineKeyboardMarkup:
    u = telebot.types.InlineKeyboardMarkup()
    u.add(telebot.types.InlineKeyboardButton('\u23F9 Stop generating', callback_data='$$$$'))
    return u

def regenMarkup(t: str) -> telebot.types.InlineKeyboardMarkup:
    u = telebot.types.InlineKeyboardMarkup()
    if len(t.encode('utf8')) < 60:
        u.add(telebot.types.InlineKeyboardButton('\u27F2 Regenerate response', callback_data=t+' $$'))
    else:
        u.add(telebot.types.InlineKeyboardButton('Response not parsed', url='https://t.me/arielgpt2bot'))
    return u

@bot.message_handler()
async def reply(message: telebot.types.Message) -> int:
    global oc
    global forceStopFlag
    global current_gpt
    global spinner
    try:
        if oc and not message.text.startswith('/reset'):
            print('Entry 1')
            await bot.reply_to(message, 'Sorry, I can only process one message at a time, otherwise the account of Ariel would be suspended.')
        else:
            if message.text.split(' ', 1)[0].startswith('/'):
                l = message.text.split(' ', 1)
                if len(l) == 1:
                    cmd = l[0]
                    arg = ''
                else:
                    cmd, arg = l
                if cmd == '/gpt' or cmd.startswith('/gpt@'):
                    if arg.strip() == '':
                        await bot.reply_to(message, "Hello, I'm here! Please say something like this:\n  <code>/gpt Who is Ariel?</code>", parse_mode='html')
                    else:
                        userid = message.from_user.id
                        oc = True
                        s = await bot.reply_to(message, f'*Processing...* \nIt may take a while. {"" if plusAccess(userid) else "Subscribe to Ariel GPT Plus for faster response."}\n\n*Tips: {random.choice(TIPS)}*', parse_mode='Markdown')
                        current_gpt = random.choice(chatgpt_plus) if plusAccess(userid) else random.choice(chatgpt)
                        r = current_gpt.ask(prompt=arg)
                        m = regenMarkup(arg)
                        m1 = stopMarkup()
                        p = ''
                        timenow = time.time()
                        for segment in r:
                            if forceStopFlag:
                                break
                            # print(f'Generating...: {segment["message"]}')
                            # print(segment)
                            if segment['message'].strip() != '':
                                p = op(segment['message'].replace('**', '*'))
                                if time.time() - timenow >= COOLDOWN:
                                    timenow = time.time()
                                else:
                                    continue
                                while True:
                                    try:
                                        await bot.edit_message_text(p+' '+ ("\u26A1" if plusAccess(userid) else spinner.spin), s.chat.id, s.message_id, reply_markup=m1, parse_mode='Markdown')
                                    except:
                                        await asyncio.sleep(15)
                                    else:
                                        break
                        if forceStopFlag:
                            await bot.edit_message_text(p+' \u2717', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
                        else:
                            if p == '':
                                p = VOID_HINT
                            await bot.edit_message_text(p+' \u25A1', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
                        oc = False
                        forceStopFlag = False

                elif cmd == '/start' or cmd.startswith('/start@'):
                    await bot.reply_to(message, "Hello, I am Ariel GPT, a LLM optimised for dialogues! Use /gpt to start chatting.")
                elif cmd == '/reset' or cmd.startswith('/reset@'):
                    forceStopFlag = False
                    [gpt.reset_chat() for gpt in chatgpt]
                    await bot.reply_to(message, "The conversation is reset.")
                elif cmd == '/me' or cmd.startswith('/me@'):
                    if plusAccess(message.from_user.id):
                        await bot.reply_to(message, f'User ID: {message.from_user.id}\nType: Plus\nExpire: Never')
                    else:
                        await bot.reply_to(message, f'User ID: {message.from_user.id}\nType: Standard\nExpire: Never')
            else:
                userid = message.from_user.id
                oc = True
                arg = message.text
                if arg.strip() == '':
                    await bot.reply_to(message, "Hello, I'm here! Please say something like this:\n  <code>/gpt Who is Ariel?</code>", parse_mode='html')
                else:
                    s = await bot.reply_to(message, f'*Processing...* \nIt may take a while. {"" if plusAccess(userid) else "Subscribe to Ariel GPT Plus for faster response."}\n\n*Tips: {random.choice(TIPS)}*', parse_mode='Markdown')
                    r = random.choice(chatgpt_plus).ask(prompt=arg) if plusAccess('userid') else current_gpt.ask(prompt=arg)
                    m = regenMarkup(arg)
                    m1 = stopMarkup()
                    p = ''
                    timenow = time.time()
                    for segment in r:
                        if forceStopFlag:
                            break
                        if segment['message'].strip() != '':
                            p = op(segment['message'].replace('**', '*'))
                            if time.time() - timenow >= COOLDOWN:
                                timenow = time.time()
                            else:
                                continue
                            while True:
                                try:
                                    await bot.edit_message_text(p+' '+ ("\u26A1" if plusAccess(userid) else spinner.spin), s.chat.id, s.message_id, reply_markup=m1, parse_mode='Markdown')
                                except:
                                    await asyncio.sleep(15)
                                else:
                                    break
                    if forceStopFlag:
                        await bot.edit_message_text(p+' \u2717', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
                    else:
                        if p == '':
                            p = VOID_HINT
                        await bot.edit_message_text(p+' \u25A1', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
                oc = False
                forceStopFlag = False

    except Exception as e:
        oc = False
        forceStopFlag = False
        print(f'Error: {e}')
        t = message.text.split(' ', 1)[-1].strip()
        m = regenMarkup(t)
        await bot.reply_to(message, f'I encountered an error while generating a response: \n\n`{e}`\n\n{ERROR_HINT}', reply_markup=m, parse_mode='Markdown')

@bot.callback_query_handler(lambda _: True)
async def callbackReply(callback_query: telebot.types.CallbackQuery):
    global oc
    global forceStopFlag
    global current_gpt
    global spinner
    try:
        if callback_query.data == '$$$$':
            if not forceStopFlag:
                forceStopFlag = True
                await bot.answer_callback_query(callback_query.id, 'OK. Stopping the generating process...')
            else:
                await bot.answer_callback_query(callback_query.id, 'No process to stop.')
            return
        if oc:
            print('Entry 2')
            await bot.reply_to(callback_query.message, 'Sorry, I can only process one message at a time, otherwise the account of Ariel would be suspended. Please wait until the last response is generated.')
        else:
            oc = True
            text = callback_query.data
            if text.endswith(' $$'):
                s = await bot.edit_message_text(f'*Processing...* \nIt may take a while.\n\n*Tips: {random.choice(TIPS)}*', callback_query.message.chat.id, callback_query.message.message_id, parse_mode='Markdown')
                text = text[:-3]
            else:
                s = await bot.reply_to(callback_query.message, f'*Processing...* \nIt may take a while.\n\n*Tips: {random.choice(TIPS)}*', parse_mode='Markdown')
            await bot.answer_callback_query(callback_query.id, 'Tips: Do not repeat questions too frequently.')
            r = current_gpt.ask(prompt=text)        
            m = regenMarkup(text)
            m1 = stopMarkup()
            p = ''
            timenow = time.time()
            for segment in r:
                if forceStopFlag:
                    break
                if segment['message'].strip() != '':
                    p = op(f'*Query: {text}* \n' + segment['message'].replace('**', '*'))
                    if time.time() - timenow >= COOLDOWN:
                        timenow = time.time()
                    else:
                        continue
                    while True:
                        try:
                            await bot.edit_message_text(p+f' {spinner.spin}', s.chat.id, s.message_id, reply_markup=m1,  parse_mode='Markdown')
                        except:
                            await asyncio.sleep(15)
                        else:
                            break
            if forceStopFlag:
                await bot.edit_message_text(p+' \u2717', s.chat.id, s.message_id, reply_markup=m,  parse_mode='Markdown')
            else:
                if p == '':
                    p = VOID_HINT
                await bot.edit_message_text(p+' \u25A1', s.chat.id, s.message_id, reply_markup=m,  parse_mode='Markdown')
            oc = False
    except Exception as e:
        oc = False
        forceStopFlag = False
        print(f'Error: {e}')
        t = text
        m = regenMarkup(t)
        await bot.reply_to(callback_query.message, f'I encountered an error while generating a response: \n\n`{e}`\n\n{ERROR_HINT}', reply_markup=m, parse_mode='Markdown')

if __name__ == '__main__':
    asyncio.run(bot.polling(non_stop=True, timeout=180))