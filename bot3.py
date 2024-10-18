from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient
import asyncio
from threading import Thread

app = Flask(__name__)

# Настройки
API_ID = '24893655'  # Ваш API ID
API_HASH = '159f9a18aa19626cwc19744ddde9b558'  # Ваш API Hash
PHONE = '+79528866327'  # Номер телефона для авторизации

# Создаем клиента
client = TelegramClient('my_bot', API_ID, API_HASH)

# Хранилище данных
user_data = {
    'keywords': [],
    'groups': [],
    'reaction_limit': 100,
    'stats': {'messages_processed': 0},
    'found_messages': []
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_authorization', methods=['POST'])
def start_authorization():
    async def authorize():
        await client.start(phone=PHONE)
        return jsonify({'status': 'success', 'message': 'Авторизация завершена.'})

    result = asyncio.run(authorize())
    return result

@app.route('/add_group', methods=['POST'])
def add_group():
    group = request.form.get('group')
    if not group:
        return jsonify({'status': 'error', 'message': 'Группа не указана.'}), 400

    user_data['groups'].append(group)
    return jsonify({'status': 'success', 'message': 'Группа добавлена.', 'groups': user_data['groups']})

@app.route('/set_keywords', methods=['POST'])
def set_keywords():
    keywords_input = request.form.get('keywords')
    if not keywords_input:
        return jsonify({'status': 'error', 'message': 'Ключевые слова не указаны.'}), 400
    
    user_data['keywords'] = [keyword.strip() for keyword in keywords_input.split(',') if keyword.strip()]
    return jsonify({'status': 'success', 'message': 'Ключевые слова установлены.', 'keywords': user_data['keywords']})

@app.route('/search_groups', methods=['POST'])
def search_groups():
    if not user_data['keywords']:
        return jsonify({'status': 'error', 'message': 'Ключевые слова не установлены.'}), 400

    found_groups = []
    
    async def search():
        await client.start()
        for keyword in user_data['keywords']:
            async for dialog in client.get_dialogs():
                if keyword.lower() in dialog.title.lower():
                    found_groups.append(dialog.title)

    try:
        asyncio.run(search())

        # Сохранение результатов в файл
        with open('found_groups.txt', 'w', encoding='utf-8') as f:
            for group in found_groups:
                f.write(f"{group}\n")
        
        return jsonify({'status': 'success', 'message': 'Группы найдены и сохранены в found_groups.txt.', 'found_groups': found_groups})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/search_results', methods=['GET'])
def search_results():
    return jsonify({
        "status": "success",
        "found_messages": user_data['found_messages']
    })

async def parse_comments_and_react():
    await client.start()
    while True:
        for group in user_data['groups']:
            async for message in client.iter_messages(group):
                user_data['stats']['messages_processed'] += 1
                if message.text and any(keyword.lower() in message.text.lower() for keyword in user_data['keywords']):
                    user_data['found_messages'].append({
                        'message_id': message.id,
                        'text': message.text
                    })
                    await message.reply('🔍 Найдено ключевое слово!')
        await asyncio.sleep(30)

@app.route('/react', methods=['POST'])
def react_to_user():
    user_id = request.form.get('user_id')
    reaction = request.form.get('reaction')

    if not user_id or not reaction:
        return jsonify({'status': 'error', 'message': 'Необходимо указать user_id и реакцию.'}), 400

    message = f'Реакция "{reaction}" отправлена пользователю {user_id}.'
    print(message)
    return jsonify({'status': 'success', 'message': message})

def run_flask():
    app.run(port=8000)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.start())
    except Exception as e:
        print(f"Ошибка при запуске клиента: {e}")

    loop.create_task(parse_comments_and_react())
    Thread(target=run_flask).start()
    
    print("Бот запущен и работает! 🎉")
