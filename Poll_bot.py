import json
import requests
from TOKEN import TOKEN

URL = f'https://api.telegram.org/bot{TOKEN}/'
admitted_users = ['sergeich97', 'dalinkevich_sergey', ]
poll_store = {}


def get_updates(last_update_id):
    parameters = {
        'timeout': 100,
        'allowed_updates': json.dumps(['poll', 'poll_answer', 'message']),
    }
    if last_update_id is not None:
        parameters['offset'] = last_update_id
    response_update = requests.get(f'{URL}getUpdates', data=parameters).content.decode('utf8')
    return json.loads(response_update)


def get_last_update_id(updates):
    update_id_array = []
    for current_update in updates['result']:
        update_id_array.append(int(current_update['update_id']))
    return max(update_id_array)


def start_bot():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if updates is not None:
            if updates['ok'] and len(updates['result']) > 0:
                last_update_id = get_last_update_id(updates) + 1
                process_updates(updates)


def process_updates(updates):
    for current_update in updates['result']:

        if current_update.get('message') is not None:
            if current_update.get('message', {}).get('text') is not None:
                username = current_update['message']['from']['username']
                if username in admitted_users:
                    text_message = current_update['message']['text']
                    chat_id = current_update['message']["chat"]["id"]
                    if text_message.strip()[:8].lower() == "bot_poll":
                        send_poll(text_message, chat_id)

        if current_update.get('poll_answer') is not None:
            if current_update.get('poll_answer', {}).get('poll_id') is not None:
                if poll_store.get(current_update['poll_answer']['poll_id']) is not None:

                    if current_update['poll_answer']['option_ids'] == [0]:
                        if current_update['poll_answer']['user']['id'] not in \
                                poll_store[current_update['poll_answer']['poll_id']]['users']:
                            poll_store[current_update['poll_answer']['poll_id']]['users'].append(
                                current_update['poll_answer']['user']['username'])

                    if not current_update['poll_answer']['option_ids']:
                        if current_update['poll_answer']['user']['id'] in \
                                poll_store[current_update['poll_answer']['poll_id']]['users']:
                            poll_store[current_update['poll_answer']['poll_id']]['users'].remove(
                                current_update['poll_answer']['user']['username'])

                    if len(poll_store[current_update['poll_answer']['poll_id']]['users']) >= \
                            poll_store[current_update['poll_answer']['poll_id']]['limit']:
                        parameters = {
                            'chat_id': poll_store[current_update['poll_answer']['poll_id']]['chat_id'],
                            'message_id': poll_store[current_update['poll_answer']['poll_id']]['message_id'],
                        }
                        response = requests.get(f'{URL}stopPoll', data=parameters)
                        send_message('Проголосовали за: \n' + '\n'.join('@' + i for i in
                                                                        poll_store[
                                                                            current_update['poll_answer']['poll_id']][
                                                                            'users']),
                                     poll_store[current_update['poll_answer']['poll_id']]['chat_id'])
                print(poll_store)


def send_message(text, chat_id):
    parameters = {
        'chat_id': chat_id,
        'text': text,
    }
    response = requests.get(f'{URL}sendMessage', data=parameters)


def send_poll(text, chat_id):
    text = text.split('\n')

    if len(text) >= 2:
        try:
            limit = int(text[0].split(' ')[1])
        except ValueError:
            limit = -1

        if limit > 0:

            parameters = {
                'chat_id': chat_id,
                'question': text[1],
                'options': json.dumps(['Да', 'Нет']),
                'is_anonymous': False,

            }
            response = requests.get(f'{URL}sendPoll', data=parameters).content.decode('utf8')
            response_js = json.loads(response)
            poll_store[response_js['result']['poll']['id']] = {
                'users': [],
                'limit': limit,
                'chat_id': chat_id,
                'message_id': response_js['result']['message_id'],
            }
        else:
            send_message('Voice_limit must be integer and >= 1', chat_id)

    else:
        send_message('Бот принимает запрос в виде: \nBot_poll voice_limit >= 1 \ndescription', chat_id)


if __name__ == '__main__':
    start_bot()
