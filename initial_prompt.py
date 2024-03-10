def get_prompt(language: str, country: str):
    assert language is not None

    language = str(language).strip().lower().capitalize()

    return f'I need help translating subtitles. ' \
           f'I will give you one line at a time. ' \
           f'Keep sensible line breaks. ' \
           f'Your replies are only translations of my input. ' \
           f'Translate into {language} ({country}).'


if __name__ == '__main__':
    print('Initial prompt, for "English":')
    print('')
    print('####################')
    print(get_prompt(language='English', country='USA'))
    print('####################')
