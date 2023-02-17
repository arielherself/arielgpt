import time
import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot
from revChatGPT.V1 import Chatbot
import local_secrets

COOLDOWN: float = 1.5

chatgpt = Chatbot(config=local_secrets.OPENAI_LOGIN_INFO)
bot = AsyncTeleBot(local_secrets.BOT_TOKEN)

print('Started.')

# prompt = "Hello!"
# response = ''
# 
# for data in chatbot.ask(prompt):
#     response = data['message']
#     print(response)

oc = False
forceStopFlag = False

def op(msg: str):
    n = msg
    try:
        n = n.replace('$$', '`')
    except Exception as e:
        print(f'Error: {e}')
    return n

def stopMarkup() -> telebot.types.InlineKeyboardMarkup:
    u = telebot.types.InlineKeyboardMarkup()
    u.add(telebot.types.InlineKeyboardButton('\u274C Stop generating', callback_data='$$$$'))
    return u

def regenMarkup(t: str) -> telebot.types.InlineKeyboardMarkup:
    u = telebot.types.InlineKeyboardMarkup()
    if len(t.encode('utf8')) < 60:
        u.add(telebot.types.InlineKeyboardButton('\u27F2 Regenerate response', callback_data=t+' $$'))
    else:
        u.add(telebot.types.InlineKeyboardButton('Response not parsed', url='https://t.me/arielsydneybot'))
    return u

@bot.message_handler()
async def reply(message: telebot.types.Message) -> int:
    global oc
    global forceStopFlag
    try:
        if oc:
            await bot.reply_to(message, 'Sorry, I can only process one message at a time, otherwise the account of Ariel would be suspended.')
        else:
            oc = True
            if message.text.split(' ', 1)[0].startswith('/'):
                l = message.text.split(' ', 1)
                if len(l) == 1:
                    cmd = l[0]
                    arg = ''
                else:
                    cmd, arg = l
                if cmd == '/gpt':
                    if arg.strip() == '':
                        await bot.reply_to(message, "Hello, I'm here! Please say something like this:\n  <code>/gpt Who is Ariel?</code>", parse_mode='html')
                    else:
                        s = await bot.reply_to(message, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
                        r = chatgpt.ask(prompt=arg)
                        m = regenMarkup(arg)
                        m1 = stopMarkup()
                        p = ''
                        timenow = time.time()
                        for segment in r:
                            if time.time() - timenow >= COOLDOWN:
                                timenow = time.time()
                            else:
                                continue
                            print('Generating...')
                            if segment['message'].strip() != '' and op(segment['message'].replace('**', '*')) != p:
                                p = op(segment['message'].replace('**', '*'))
                                try:
                                    await bot.edit_message_text(p+' ...', s.chat.id, s.message_id, reply_markup=m1, parse_mode='Markdown')
                                except:
                                    pass
                        await bot.edit_message_text(p+' \u25A1', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')

                elif cmd == '/start':
                    await bot.reply_to(message, "Hello, I am Ariel GPT, a LLM optimised for dialogues! Use /gpt to start chatting.")
            else:
                arg = message.text
                if arg.strip() == '':
                    await bot.reply_to(message, "Hello, I'm here! Please say something like this:\n  <code>/gpt Who is Ariel?</code>", parse_mode='html')
                else:
                    s = await bot.reply_to(message, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
                    r = chatgpt.ask(prompt=arg)
                    m = regenMarkup(arg)
                    m1 = stopMarkup()
                    p = ''
                    timenow = time.time()
                    for segment in r:
                        if forceStopFlag:
                            break
                        if time.time() - timenow >= COOLDOWN:
                            timenow = time.time()
                        else:
                            continue
                        if segment['message'].strip() != '' and op(segment['message'].replace('**', '*')) != p:
                            p = op(segment['message'].replace('**', '*'))
                            try:
                                await bot.edit_message_text(p+' ...', s.chat.id, s.message_id, reply_markup=m1, parse_mode='Markdown')
                            except:
                                pass
                    if forceStopFlag:
                        await bot.edit_message_text(p+' \u2717', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
                    else:
                        await bot.edit_message_text(p+' \u25A1', s.chat.id, s.message_id, reply_markup=m, parse_mode='Markdown')
            oc = False
            forceStopFlag = False
    except Exception as e:
        oc = False
        forceStopFlag = False
        print(f'Error: {e}')
        if message.text.startswith('/gpt '):
            t = message.text[message.text.find('/gpt ')+5:].strip()
        else:
            t = message.text.strip()
        m = regenMarkup(t)
        await bot.reply_to(message, f'I encountered an error while generating a response: \n\n<code>{e}</code>', reply_markup=m, parse_mode='html')

@bot.callback_query_handler(lambda _: True)
async def callbackReply(callback_query: telebot.types.CallbackQuery):
    global oc
    global forceStopFlag
    try:
        if callback_query.message == '$$$$':
            forceStopFlag = True
            return
        if oc:
            await bot.reply_to(callback_query.message, 'Sorry, I can only process one message at a time, otherwise the account of Ariel would be suspended. Please wait until the last response is generated.')
        else:
            oc = True
            text = callback_query.data
            if text.endswith(' $$'):
                s = await bot.edit_message_text('*Processing...* \nIt may take a while.', callback_query.message.chat.id, callback_query.message.message_id, parse_mode='Markdown')
                text = text[:-3]
            else:
                s = await bot.reply_to(callback_query.message, '*Processing...* \nIt may take a while.', parse_mode='Markdown')
            r = chatgpt.ask(prompt=text)        
            m = regenMarkup(text)
            m1 = stopMarkup()
            p = ''
            timenow = time.time()
            for segment in r:
                if forceStopFlag:
                    break
                if time.time() - timenow >= COOLDOWN:
                    timenow = time.time()
                else:
                    continue
                if segment['message'].strip() != '' and op(segment['message'].replace('**', '*')) != p:
                    p = op(f'*Query: {text}* \n' + segment['message'].replace('**', '*'))
                    try:
                        await bot.edit_message_text(p+' ...', s.chat.id, s.message_id, reply_markup=m1,  parse_mode='Markdown')
                    except:
                        pass
            if forceStopFlag:
                await bot.edit_message_text(p+' \u2717', s.chat.id, s.message_id, reply_markup=m,  parse_mode='Markdown')
            else:
                await bot.edit_message_text(p+' \u25A1', s.chat.id, s.message_id, reply_markup=m,  parse_mode='Markdown')
            oc = False
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(bot.polling(non_stop=True, timeout=180))