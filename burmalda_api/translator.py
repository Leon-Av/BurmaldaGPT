import re
from typing import List, Optional

DICTIONARY = {
    # местоимения
    'я': 'ч',
    'меня': 'менч',
    'мне': 'мье',
    'мной': 'чой',
    'мною': 'чою',
    'мой': 'мок',
    'моя': 'моч',
    'моё': 'моё',
    'мое': 'моё',
    'мои': 'мои',
    'моего': 'мокого',
    'моему': 'мокому',
    'моим': 'моким',
    'моей': 'мокой',
    'мы': 'мч',
    'нас': 'насч',
    'нам': 'намч',
    'нами': 'намчи',
    'наш': 'нашч',
    'наша': 'нашча',
    'наше': 'нашче',
    'наши': 'нашчи',
    # семья и люди
    'друг': 'друн',
    'друга': 'друна',
    'другу': 'друну',
    'другом': 'друном',
    'друге': 'друне',
    'друзья': 'друны',
    'друзей': 'друнов',
    'друзьям': 'друнам',
    'друзьями': 'друнами',
    'сын': 'сыр',
    'сына': 'сыра',
    'сыну': 'сыру',
    'сыном': 'сыром',
    'сыне': 'сыре',
    'сыновья': 'сыры',
    'сыновей': 'сыров',
    'жена': 'жинка',
    'жену': 'жинку',
    'жене': 'жинке',
    'женой': 'жинкой',
    'жены': 'жинки',
    'папа': 'батч',
    'папы': 'батчи',
    'папе': 'батче',
    'папу': 'батча',
    'папой': 'батчом',
    'отец': 'отчовство',
    'отца': 'отчовства',
    'отцу': 'отчовству',
    'отцом': 'отчовством',
    'бать': 'батч',
    'батя': 'батч',
    # дед/прадед
    'дед': 'дод',
    'деда': 'дода',
    'деду': 'доду',
    'дедом': 'додом',
    'деде': 'доде',
    'деды': 'доды',
    'дедов': 'додов',
    'прадед': 'прадод',
    'прадеда': 'прадода',
    'прадеду': 'прадоду',
    'прадедом': 'прадодом',
    # кот/кошка
    'кот': 'котость',
    'кота': 'котости',
    'коту': 'котости',
    'котом': 'котостью',
    'коте': 'котосте',
    'коты': 'котости',
    'котов': 'котостей',
    'кошка': 'кошкость',
    'кошку': 'кошкость',
    'кошке': 'кошкости',
    'кошки': 'кошкости',
    'кошек': 'кошкостей',
    # школа
    'школа': 'школость',
    'школу': 'школость',
    'школе': 'школости',
    'школой': 'школости',
    'школы': 'школости',
    'школ': 'школостьей',
    'школьник': 'школьникость',
    'школьница': 'школьницость',
    # бурмалд- приставка
    'телефон': 'бурмалдфон',
    'телефона': 'бурмалдфона',
    'телефону': 'бурмалдфону',
    'телефоном': 'бурмалдфоном',
    'телефоне': 'бурмалдфоне',
    'телефоны': 'бурмалдфоны',
    'телефонов': 'бурмалдфонов',
    'заяц': 'бурмалдаяц',
    'зайца': 'бурмалдаяца',
    'зайцу': 'бурмалдаяцу',
    'зайцем': 'бурмалдаяцем',
    'зайце': 'бурмалдаяце',
    'зайцы': 'бурмалдаяцы',
    'зайцев': 'бурмалдаяцев',
    'заяцъ': 'бурмалдаяц',
    'птички': 'бурмалдички',
    'птичка': 'бурмалдичка',
    'птичку': 'бурмалдичку',
    'птичке': 'бурмалдичке',
    'птичкой': 'бурмалдичкой',
    'птица': 'бурмалдица',
    'птицу': 'бурмалдицу',
    'птицы': 'бурмалдицы',
    'перекресток': 'бурмалкресток',
    'перекрёсток': 'бурмалкресток',
    'перекрестка': 'бурмалкрестка',
    'перекрёстка': 'бурмалкрестка',
    'перекрестке': 'бурмалкрестке',
    'перекрёстке': 'бурмалкрестке',
    # прилагательные → существительные
    'сладкий': 'сладость',
    'сладкая': 'сладость',
    'сладкое': 'сладость',
    'сладкие': 'сладость',
    'сладкого': 'сладости',
    'сладкому': 'сладости',
    'сладким': 'сладостью',
    'сладкой': 'сладостью',
    'сладкую': 'сладость',
    'сладко': 'сладостно',
    'приятный': 'приятность',
    'приятная': 'приятность',
    'приятное': 'приятность',
    'приятные': 'приятности',
    'приятно': 'приятностно',
    'вкусный': 'вкусность',
    'вкусная': 'вкусность',
    'вкусное': 'вкусность',
    'вкусные': 'вкусности',
    'вкусно': 'вкусностно',
    # неизменяемые исключения
    'бурмалда': 'бурмалда',
    'мурино': 'мурино',
    'село': 'село',
    'молочное': 'молочное',
    'эпштейн': 'эпштейн',
    'чекушка': 'чекушка',
    'чекушки': 'чекушки',
    'чекушку': 'чекушку',
    'всеми': 'всеми',
    'ведь': 'ведь',
    'вопреки': 'вопреки',
    'даже': 'даже',
    'практически': 'практически',
    'смотря': 'смотря',
    'шел': 'шел',
    'сели': 'сели',
    'было': 'было',
    'былт': 'былт',
    'находимся': 'находимся',
    'переночевав': 'переночевав',
    'летает': 'летает',
    'помню': 'помню',
    'явилась': 'явилась',
    'отдана': 'отдана',
    # общага/этаж/деньги/мем
    'общага': 'общагость',
    'общагу': 'общагость',
    'общаге': 'общагости',
    'этаж': 'этажность',
    'этажа': 'этажности',
    'этажу': 'этажности',
    'этажом': 'этажностью',
    'деньги': 'деньгость',
    'деньгам': 'деньгость',
    'деньгами': 'деньгость',
    'мем': 'мемность',
    'мемы': 'мемности',
    'меллстрой': 'меллстройность',
    'бурмалдит': 'бурмалдит',
    'дядя': 'дядность',
    'дяди': 'дядности',
    'дяде': 'дядности',
    'дядю': 'дядностю',
    'дядей': 'дядностью',
    'учительница': 'учиха',
    'учительницы': 'учихи',
    'учительницу': 'учиху',
    'сладость': 'сладость',
    'сладости': 'сладости',
    'сладостью': 'сладостью',
    'приятность': 'приятность',
    'приятности': 'приятности',
    'приятностью': 'приятностью',
    'вкусность': 'вкусность',
    'вкусности': 'вкусности',
    'вкусностью': 'вкусностью',
    'дела': 'дела',
    'туман': 'фог',
    'тумана': 'фога',
    'туману': 'фогу',
    'туманом': 'фогом',
    'муринск': 'муринскость',
    'кто': 'кьо',
    'то': 'ьо',
    'что': 'чьо',
    'это': 'эьо',
    'множество': 'множество',
    'был': 'был',
    'была': 'была',
    'были': 'были',
}

STOP_WORDS = {
    'и','а','но','или','либо','да','же','ли','бы','не','ни','ну','вот',
    'этот','эта','эти','так','как',
    'что','чтобы','когда','если','пока','потому','поэтому','где','куда',
    'откуда','зачем','почему','кого','кому','кем',
    'о','об','про','для','без','до','после','перед','при','над','под',
    'из','от','у','к','ко','с','со','на','в','во','за','по','через',
    'между','около','возле','внутри','снаружи',
    'тут','там','здесь','сюда','туда',
    'очень','уже','ещё','еще','тоже','только','просто','почти',
    'прям','вообще','примерно',
    'быстро','сейчас','потом','теперь','сегодня','завтра','вчера',
    'всегда','никогда','иногда','может','можно','нельзя','надо','нужно',
    'пусть','давай','давайте',
    'он','она','оно','они','его','её','ее','ему','ей','им','их','ими',
    'себя','себе','собой',
    'твой','твоя','твоё','твое','ваш','ваша','ваши',
    'тот','та','те','все','всё','всех','всем','сам','сама','сами',
    'один','одна','одно','два','две','три','четыре','пять','шесть',
    'семь','восемь','девять','десять',
    'блин','короче','типа','ладно','ага','нет','да',
    'свой','своя','своё','свое','свои',
}

COMMON_VERBS = {
    'быть','есть','был','была','было','были','буду','будешь','будет',
    'будем','будете','будут',
    'идти','иду','идешь','идёшь','идет','идёт','идем','идём','идете',
    'идёте','идут','шёл','шла','шло','шли','пошел','пошёл','пошла','пошли',
    'ехать','еду','едешь','едет','едем','едете','едут','ехал','ехала','ехали',
    'находиться','нахожусь','находишься','находится','находимся','находитесь','находятся',
    'смотреть','смотрю','смотришь','смотрит','смотрим','смотрите','смотрят',
    'ходить','хожу','ходишь','ходит','ходим','ходите','ходят',
    'сказать','сказал','сказала','сказали','говорить','говорю','говоришь','говорит','говорим','говорят',
    'делать','делаю','делаешь','делает','делаем','делаете','делают','сделал','сделала','сделали',
    'бурмалдить','бурмалдю','бурмалдишь','бурмалдит','бурмалдим','бурмалдите','бурмалдят',
    'хотеть','хочу','хочешь','хочет','хотим','хотите','хотят',
    'мочь','могу','можешь','может','можем','можете','могут',
    'знать','знаю','знаешь','знает','знаем','знаете','знают',
    'видеть','вижу','видишь','видит','видим','видите','видят','увидел','увидела','увидели',
    'купить','купил','купила','купили','куплю','купишь','купит',
    'взять','взял','взяла','взяли','беру','берешь','берёшь','берет','берёт','берут',
    'дать','дал','дала','дали','даю','даешь','даёшь','дает','даёт','дают',
    'жить','живу','живешь','живёшь','живет','живёт','живут',
    'любить','люблю','любишь','любит','любят',
    'писать','пишу','пишешь','пишет','пишут',
    'читать','читаю','читаешь','читает','читают',
    'перевести','переводить','перевел','перевёл','перевела','перевели',
    'работать','работаю','работаешь','работает','работают',
    'учиться','учусь','учишься','учится','учимся','учатся',
    'играть','играю','играешь','играет','играют',
    'спать','сплю','спишь','спит','спят',
    'пить','пью','пьешь','пьёшь','пьет','пьёт','пьют',
    'помнить','помню','помнишь','помнит','помним','помните','помнят',
    'помнил','помнила','помнили',
    'явиться','явился','явилась','явилось','явились','явлюсь','явишься','явится','явятся',
    'появиться','появился','появилась','появилось','появились',
    'родиться','родился','родилась','родилось','родились',
    'оказаться','оказался','оказалась','оказалось','оказались',
    'казаться','казался','казалась','казалось','казались',
    'смеяться','смеюсь','смеешься','смеётся','смеются','смеялся','смеялась','смеялись',
    'бояться','боюсь','боишься','боится','боятся','боялся','боялась','боялись',
    'нравиться','нравлюсь','нравишься','нравится','нравятся',
    'вернуться','вернулся','вернулась','вернулось','вернулись',
    'улыбаться','улыбаюсь','улыбаешься','улыбается','улыбаются',
    'лежать','лежу','лежишь','лежит','лежат','лежал','лежала','лежали',
    'стоять','стою','стоишь','стоит','стоят','стоял','стояла','стояли',
    'сесть','сел','села','село','сели','сяду','сядешь','сядет','сядем','сядете','сядут',
    'сидеть','сижу','сидишь','сидит','сидят','сидел','сидела','сидели',
    'бежать','бегу','бежишь','бежит','бегут','бежал','бежала','бежали',
    'лететь','лечу','летишь','летит','летят','летел','летела','летели',
    'летать','летаю','летаешь','летает','летаем','летаете','летают',
    'нести','несу','несешь','несёшь','несет','несёт','несут','нес','нёс','несла','несли',
    'вести','веду','ведешь','ведёшь','ведет','ведёт','ведут','вел','вёл','вела','вели',
    'прийти','пришел','пришёл','пришла','пришли','приду','придешь','придёт',
    'уйти','ушел','ушёл','ушла','ушли','уйду','уйдешь','уйдёт',
    'найти','нашел','нашёл','нашла','нашли','найду','найдешь','найдёт',
    'понять','понял','поняла','поняли','понимаю','понимаешь','понимает','понимают',
    'получить','получил','получила','получили','получу','получишь','получит','получают',
    'ждать','жду','ждешь','ждёшь','ждет','ждёт','ждут','ждал','ждала','ждали',
    'искать','ищу','ищешь','ищет','ищут','искал','искала','искали',
    'слушать','слушаю','слушаешь','слушает','слушают','слушал','слушала','слушали',
    'слышать','слышу','слышишь','слышит','слышат',
    'открыть','открыл','открыла','открыли','открою','откроешь','откроет',
    'закрыть','закрыл','закрыла','закрыли','закрою','закроешь','закроет',
    'поехать','поехал','поехала','поехали','поеду','поедешь','поедет',
    'посмотреть','посмотрю','посмотришь','посмотрит','посмотрят',
    'сказать','скажу','скажешь','скажет','скажут',
    'сделать','сделаю','сделаешь','сделает','сделают',
    'увидеть','увижу','увидишь','увидит','увидят',
    'купить','куплю','купишь','купит','купят',
    'пойти','пойду','пойдешь','пойдёт','пойдут',
    'побежать','побегу','побежишь','побежит','побегут',
    'полететь','полечу','полетишь','полетит','полетят',
    'захотеть','захочу','захочешь','захочет','захотят',
    'смочь','смогу','сможешь','сможет','смогут',
}

VERB_ENDINGS_PATTERN = re.compile(
    r'(ться|тся|ешь|ёшь|ете|ёте|ите|ать|ять|еть|ить|оть|уть|ти|чь|'
    r'аю|яю|ею|ую|юю|ишь|ит|им|ат|ят|ет|ют|ут|'
    r'ал|ял|ел|ил|ла|ло|ли)$'
)

PARTICIPLE_ENDINGS = re.compile(
    r'(анный|анная|анное|анные|енного|енному|енным|енными|'
    r'енный|енная|енное|енные|ённый|ённая|ённое|ённые|'
    r'вший|вшая|вшее|вшие|ющий|ющая|ющее|ющие|'
    r'имый|имая|имое|имые|емый|емая|емое|емые)$'
)

SHORT_PARTICIPLE = re.compile(r'^(.*?)(ан|ана|ано|аны|ян|яна|яно|яны|ен|ена|ено|ены|ён|ёна|ёно|ёны|т|та|то|ты)$')

GERUND_PATTERN = re.compile(
    r'(ав|яв|ев|ёв|ив|ыв|ув|вши|вшись|ившись|авшись|явшись|евшись|увшись)$'
)

PAST_TENSE_REFLEXIVE = re.compile(
    r'(лся|лась|лось|лись|ался|алась|алось|ались|ился|илась|илось|ились|'
    r'елся|елась|елось|елись|ялся|ялась|ялось|ялись)$'
)

PRESENT_TENSE = re.compile(
    r'(аешь|ает|аем|аете|ают|яешь|яет|яем|яете|яют|'
    r'еешь|еет|еем|еете|еют|уешь|ует|уем|уете|уют|'
    r'ишь|ит|им|ите|ат|ят|ешь|ёшь|ете|ёте|ют|ут|ем)$'
)

REFLEXIVE_PRESENT = re.compile(
    r'(ешься|ёшься|ишься|аемся|яемся|еемся|уемся|емся|имся|'
    r'аетесь|яетесь|еетесь|уетесь|етесь|итесь|'
    r'ается|яется|еется|уется|ется|ётся|ится|'
    r'аются|яются|еются|уются|утся|ются|атся|ятся)$'
)

ADJECTIVE_ENDINGS = [
    'ый','ий','ой','ая','яя','ое','ее','ые','ие',
    'ого','его','ому','ему','ом','ем','ым','им','ой','ей','ую','юю',
    'ых','их','ыми','ими'
]

SUFFIX_EXCEPTION_RULES = [
    {
        'name': 'дед → дод',
        'allow_any_prefix': True,
        'pairs': [
            ('дедами','додами'),('дедах','додах'),('дедам','додам'),
            ('дедов','додов'),('дедом','додом'),('деда','дода'),
            ('деду','доду'),('деде','доде'),('деды','доды'),('дед','дод'),
        ]
    },
    {
        'name': 'кот → котость',
        'allow_any_prefix': True,
        'pairs': [
            ('котами','котостями'),('котах','котостях'),('котам','котостям'),
            ('котов','котостей'),('котом','котостью'),('кота','котость'),
            ('коту','котости'),('коте','котости'),('коты','котости'),('кот','котость'),
        ]
    },
    {
        'name': 'кошка → кошкость',
        'allow_any_prefix': True,
        'pairs': [
            ('кошками','кошкостями'),('кошках','кошкостях'),('кошкам','кошкостям'),
            ('кошек','кошкостей'),('кошкой','кошкостью'),('кошка','кошкость'),
            ('кошку','кошкость'),('кошке','кошкости'),('кошки','кошкости'),
        ]
    },
    {
        'name': 'школа → школость',
        'allow_any_prefix': True,
        'pairs': [
            ('школами','школостями'),('школах','школостях'),('школам','школостям'),
            ('школой','школостью'),('школу','школость'),('школе','школости'),
            ('школы','школости'),('школа','школость'),('школ','школостьей'),
        ]
    },
]

BURMAL_PREFIX_WORDS = {
    'дом','дома','дому','домом','доме',
    'город','города','городу','городом','городе',
    'лес','леса','лесу','лесом','лесе',
    'магазин','магазина','магазину','магазином','магазине',
    'компьютер','компьютера','компьютеру','компьютером','компьютере',
    'ноутбук','ноутбука','ноутбуку','ноутбуком','ноутбуке',
    'интернет','интернета','интернету','интернетом','интернете',
    'чат','чата','чату','чатом','чате',
    'переводчик','переводчика','переводчику','переводчиком','переводчике',
    'стол','стола','столу','столом','столе',
    'окно','окна','окну','окном','окне',
}

AGREEMENT_INSTRUMENTAL = {
    'твоим': 'твоей', 'вашим': 'вашей', 'своим': 'своей',
    'моим': 'мокой', 'нашим': 'нашчей', 'этим': 'этой',
    'тем': 'той', 'каким': 'какой', 'одним': 'одной',
    'дорогим': 'дорогой', 'строгим': 'строгой', 'мягким': 'мягкой',
    'маленьким': 'маленькой', 'хорошим': 'хорошей', 'плохим': 'плохой',
    'чистым': 'чистой', 'новым': 'новой', 'старым': 'старой',
    'красивым': 'красивой', 'большим': 'большой',
    'любым': 'любой', 'сладким': 'сладкой', 'вкусным': 'вкусной',
    'приятным': 'приятной', 'сильным': 'сильной',
}

AGREEMENT_SOFT = {
    'твоему': 'твоей', 'твоем': 'твоей', 'твоём': 'твоей', 'твоей': 'твоей',
    'вашему': 'вашей', 'вашем': 'вашей', 'вашей': 'вашей',
    'своему': 'своей', 'своем': 'своей', 'своём': 'своей', 'своей': 'своей',
    'моему': 'мокой', 'моем': 'мокой', 'моём': 'мокой', 'моей': 'мокой',
    'нашему': 'нашчей', 'нашем': 'нашчей', 'нашей': 'нашчей',
    'этому': 'этой', 'этом': 'этой', 'этой': 'этой',
    'тому': 'той', 'том': 'той', 'той': 'той',
}

AGREEMENT_DIRECT = {
    'твой': 'твоя', 'твоего': 'твою', 'твою': 'твою',
    'ваш': 'ваша', 'вашего': 'вашу', 'вашу': 'вашу',
    'свой': 'своя', 'своего': 'свою', 'свою': 'свою',
    'мой': 'мока', 'моего': 'моку', 'мою': 'моку',
    'наш': 'нашча', 'нашего': 'нашчу', 'нашу': 'нашчу',
    'этот': 'эта', 'этого': 'эту', 'эту': 'эту',
    'тот': 'та', 'того': 'ту', 'ту': 'ту',
}


def _is_russian_word(token: str) -> bool:
    return bool(re.fullmatch(r'[А-Яа-яЁё]+', token))


def _keep_case(source: str, translated: str) -> str:
    if not source or not translated:
        return translated
    if source == source.upper() and len(source) > 1:
        return translated.upper()
    if source[0].isupper() and source[1:].islower():
        return translated[0].upper() + translated[1:]
    return translated


def _looks_like_verb(word: str) -> bool:
    low = word.lower()
    if low in COMMON_VERBS:
        return True
    if len(low) <= 3:
        return False
    if PARTICIPLE_ENDINGS.search(low):
        return True
    if SHORT_PARTICIPLE.match(low) and len(low) >= 5:
        return True
    if re.search(r'(ться|тся|ать|ять|еть|ить|оть|уть|чь|сти|зти|сть)$', low):
        return True
    if GERUND_PATTERN.search(low) and len(low) >= 5:
        return True
    if PAST_TENSE_REFLEXIVE.search(low) and len(low) >= 5:
        return True
    if REFLEXIVE_PRESENT.search(low):
        return True
    if PRESENT_TENSE.search(low):
        return True
    low_gerunds = {'смотря','говоря','глядя','исходя','стоя','сидя','идя','шутя','молчая','играя','думая','делая'}
    if low in low_gerunds:
        return True
    if len(low) >= 5 and re.search(r'(аю|яю|ею|ую|юю|ою|ню|мню|влю|блю|плю|флю|жду|щу)$', low):
        return True
    if len(low) >= 4 and re.search(r'(али|яли|ели|или|ыли)$', low):
        return True
    if len(low) >= 5 and re.search(r'(ал|ял|ел|ил|ол|ул|ала|яла|ела|ила|ола|ула|али|яли|ели|или|оли|ули|ало|яло|ело|ило|оло|уло)$', low):
        return True
    return False


def _looks_like_adjective(word: str) -> bool:
    low = word.lower()
    if len(low) <= 4:
        return False
    if re.search(r'(строй|бой|рой|слой)$', low):
        return False
    return any(low.endswith(e) for e in ADJECTIVE_ENDINGS)


def _translate_by_pattern(lower: str) -> Optional[str]:
    for rule in SUFFIX_EXCEPTION_RULES:
        for src, dst in rule['pairs']:
            if not lower.endswith(src):
                continue
            prefix = lower[:-len(src)]
            if not rule.get('allow_any_prefix', False) and prefix:
                continue
            return prefix + dst
    return None


def _translate_enyee_enie(word: str) -> Optional[str]:
    if len(word) < 6:
        return None
    if word.endswith('енье') or word.endswith('ение'):
        return word[:-4] + 'енность'
    if word.endswith('енья') or word.endswith('ения'):
        return word[:-4] + 'енности'
    if word.endswith('енью') or word.endswith('ению'):
        return word[:-4] + 'енности'
    if word.endswith('еньем') or word.endswith('ением'):
        return word[:-5] + 'енностью'
    return None


def _translate_mya_noun(word: str) -> Optional[str]:
    if word.endswith('мя'):
        return word[:-1] + 'еность'
    if word.endswith('мени'):
        return word[:-4] + 'менности'
    if word.endswith('менем'):
        return word[:-5] + 'менностью'
    return None


def _translate_ica_noun(word: str) -> Optional[str]:
    if word.endswith('ицами'): return word[:-5] + 'очностями'
    if word.endswith('ицах'): return word[:-4] + 'очностях'
    if word.endswith('ицам'): return word[:-4] + 'очностям'
    if word.endswith('ицей') or word.endswith('ицею'): return word[:-4] + 'очностью'
    if word.endswith('ице'): return word[:-3] + 'очности'
    if word.endswith('ицу'): return word[:-3] + 'очность'
    if word.endswith('ицы'): return word[:-3] + 'очности'
    if word.endswith('ица'): return word[:-3] + 'очность'
    return None


def _translate_cia_noun(word: str) -> Optional[str]:
    if word.endswith('циями'): return word[:-5] + 'чностями'
    if word.endswith('циях'): return word[:-4] + 'чностях'
    if word.endswith('циям'): return word[:-4] + 'чностям'
    if word.endswith('цией') or word.endswith('циею'): return word[:-4] + 'чностью'
    if word.endswith('ции'): return word[:-3] + 'чности'
    if word.endswith('цию'): return word[:-3] + 'чность'
    if word.endswith('ция'): return word[:-3] + 'чность'
    return None


def _translate_alternating_feminine(word: str) -> Optional[str]:
    if word.endswith('огами'): return word[:-5] + 'ожностями'
    if word.endswith('огах'): return word[:-4] + 'ожностях'
    if word.endswith('огам'): return word[:-4] + 'ожностям'
    if word.endswith('огой') or word.endswith('огою'): return word[:-4] + 'ожностью'
    if word.endswith('ога'): return word[:-3] + 'ожность'
    if word.endswith('огу'): return word[:-3] + 'ожность'
    if word.endswith('оге'): return word[:-3] + 'ожности'
    if word.endswith('оги'): return word[:-3] + 'ожности'
    if word.endswith('овами'): return word[:-5] + 'овностями'
    if word.endswith('овах'): return word[:-4] + 'овностях'
    if word.endswith('овам'): return word[:-4] + 'овностям'
    if word.endswith('овой') or word.endswith('овою'): return word[:-4] + 'овностью'
    if word.endswith('ова'): return word[:-3] + 'овность'
    if word.endswith('ову'): return word[:-3] + 'овность'
    if word.endswith('ове'): return word[:-3] + 'овности'
    if word.endswith('овы'): return word[:-3] + 'овности'
    return None


def _translate_ina_noun(word: str) -> Optional[str]:
    if len(word) < 6:
        return None
    if word.endswith('инами'): return word[:-5] + 'иностями'
    if word.endswith('инах'): return word[:-4] + 'иностях'
    if word.endswith('инам'): return word[:-4] + 'иностям'
    if word.endswith('иной') or word.endswith('иною'): return word[:-4] + 'инностью'
    if word.endswith('ина'): return word[:-3] + 'инность'
    if word.endswith('ину'): return word[:-3] + 'инность'
    if word.endswith('ине'): return word[:-3] + 'инности'
    if word.endswith('ины'): return word[:-3] + 'инность'
    return None


def _translate_eyka_noun(word: str) -> Optional[str]:
    if len(word) < 7:
        return None
    if word.endswith('ейками'): return word[:-6] + 'еичностями'
    if word.endswith('ейках'): return word[:-5] + 'еичностях'
    if word.endswith('ейкам'): return word[:-5] + 'еичностям'
    if word.endswith('ейкой') or word.endswith('ейкою'): return word[:-5] + 'еичностью'
    if word.endswith('ейка'): return word[:-4] + 'еичность'
    if word.endswith('ейку'): return word[:-4] + 'еичность'
    if word.endswith('ейке'): return word[:-4] + 'еичности'
    if word.endswith('ейки'): return word[:-4] + 'еичности'
    return None


def _translate_ov_genitive_plural(word: str) -> Optional[str]:
    if len(word) < 6:
        return None
    if word.endswith('одов'):
        return word[:-2] + 'ности'
    if word.endswith('ов'):
        return word[:-2] + 'ности'
    return None


def _translate_ami_instrumental_plural(word: str) -> Optional[str]:
    if len(word) < 6:
        return None
    if word.endswith('ами'):
        return word[:-3] + 'ностями'
    if word.endswith('ями'):
        return word[:-3] + 'ностями'
    return None


def _translate_nik_noun(word: str) -> Optional[str]:
    if len(word) < 6:
        return None
    if word.endswith('никами'): return word[:-6] + 'ностями'
    if word.endswith('никах'): return word[:-5] + 'ностях'
    if word.endswith('никам'): return word[:-5] + 'ностям'
    if word.endswith('ников'): return word[:-5] + 'ностей'
    if word.endswith('ником'): return word[:-5] + 'ностью'
    if word.endswith('ника'): return word[:-4] + 'ности'
    if word.endswith('нику'): return word[:-4] + 'ности'
    if word.endswith('нике'): return word[:-4] + 'ности'
    if word.endswith('ники'): return word[:-4] + 'ности'
    if word.endswith('ник'): return word[:-3] + 'ность'
    return None


def _translate_soft_neuter_like_pole(word: str) -> Optional[str]:
    if len(word) < 4:
        return None
    if word.endswith('е') or word.endswith('ё'):
        return word[:-1] + 'есть'
    if word.endswith('ю'):
        return word[:-1] + 'ести'
    if word.endswith('ем') or word.endswith('ём'):
        return word[:-2] + 'естью'
    if word.endswith('я'):
        return word[:-1] + 'ести'
    if word.endswith('ей'):
        return word[:-2] + 'естей'
    return None


def _translate_case_noun_to_nost(word: str, prev: str) -> Optional[str]:
    if len(word) < 5:
        return None
    prev_low = prev.lower() if prev else ''

    if word.endswith('у'):
        base = word[:-1]
        if re.search(r'[кгх]$', base):
            return None
        if prev_low in ('к', 'ко'):
            return base + 'ности'
        if prev_low in ('в', 'во', 'на', 'за', 'через', 'про'):
            return base + 'ность'
        if re.search(r'(ину|ыну|ану|яну|ону|уну|ену)$', word):
            return base + 'ность'
        if re.search(r'(ент|ист|ник|ик|ер|ор|ар|ир|тел|тель|чик|щик)$', base):
            return base + 'ности'
        return base + 'ность'

    if word.endswith('а') or word.endswith('я'):
        base = word[:-1]
        if prev_low in ('от', 'до', 'из', 'без', 'для', 'у', 'около', 'возле', 'вокруг'):
            return base + 'ности'
        if prev_low in ('в', 'во', 'на', 'за'):
            return base + 'ность'

    if word.endswith('иям'):
        return word[:-3] + 'ностям'
    if word.endswith('ам') or word.endswith('ям'):
        return word[:-2] + 'ностям'

    if word.endswith('ю'):
        base = word[:-1]
        if prev_low in ('к', 'ко'):
            return base + 'ности'

    if word.endswith('ой') or word.endswith('ою'):
        base = word[:-2] if word.endswith('ою') else word[:-2]
        if prev_low in ('с', 'со', 'под', 'над', 'перед'):
            return base + 'остью'

    return None


def _translate_contextual_phrase(lower: str, prev: str, prev_prev: str) -> Optional[str]:
    if prev_prev == 'по' and prev == 'обе' and lower.endswith('ы'):
        return lower[:-1] + 'ностям'
    return None


def _add_ost_or_nost(word: str) -> str:
    if word.endswith('ость') or word.endswith('ность'):
        return word

    if re.search(r'(ода|еда|ида)$', word):
        return word[:-1] + 'ность'
    if word.endswith('а'):
        return word[:-1] + 'ость'
    if word.endswith('я'):
        return word[:-1] + 'ность'
    if word.endswith('ь'):
        return word[:-1] + 'ность'
    if word.endswith('й'):
        return word + 'ность'
    if word.endswith('о'):
        return word[:-1] + 'ость'
    if word.endswith('е'):
        return word[:-1] + 'есть'
    if word.endswith('и'):
        return word[:-1] + 'ичность'
    if word.endswith('ы'):
        return word[:-1] + 'ость'
    if re.search(r'[чщжшц]$', word):
        return word + 'ность'

    return word + 'ость'


def _burmalize_with_prefix(word: str) -> str:
    if word.startswith('бурмал'):
        return word
    if re.match(r'^[аеёиоуыэюя]', word):
        return 'бурмалд' + word
    if word[0] in 'птд':
        return 'бурмалд' + word
    return 'бурмал' + word


def _should_translate_as_noun(word: str, hard: bool = True) -> bool:
    low = word.lower()
    if len(low) <= 2:
        return False
    if low in STOP_WORDS:
        return False
    if _looks_like_verb(low):
        return False
    if _looks_like_adjective(low):
        return False
    if low.endswith('о') and len(low) > 5 and low not in ('окно','кино','метро'):
        return False
    if not hard and len(low) < 5:
        return False
    return True


def _get_ost_form_type(translated: str) -> Optional[str]:
    low = translated.lower()
    if low.endswith('остью') or low.endswith('ностью'):
        return 'instrumental'
    if low.endswith('остями') or low.endswith('ностями'):
        return 'instrumental_plural'
    if low.endswith('остях') or low.endswith('ностях'):
        return 'prepositional_plural'
    if low.endswith('остям') or low.endswith('ностям'):
        return 'dative_plural'
    if low.endswith('остей') or low.endswith('ностей'):
        return 'genitive_plural'
    if low.endswith('ости') or low.endswith('ности'):
        return 'soft'
    if low.endswith('ость') or low.endswith('ность'):
        return 'direct'
    if low.endswith('осте') or low.endswith('носте'):
        return 'soft'
    return None


def _convert_adjective_to_feminine(source: str, form_type: str) -> Optional[str]:
    low = source.lower()

    if form_type == 'instrumental':
        exact = {
            'большим': 'большой', 'дорогим': 'дорогой', 'строгим': 'строгой',
            'мягким': 'мягкой', 'маленьким': 'маленькой', 'хорошим': 'хорошей',
            'плохим': 'плохой', 'чистым': 'чистой', 'новым': 'новой',
            'старым': 'старой', 'красивым': 'красивой',
        }
        if low in exact:
            return exact[low]
        if low.endswith('ым'):
            return low[:-2] + 'ой'
        if low.endswith('им'):
            stem = low[:-2]
            return stem + 'ой' if re.search(r'[гкх]$', stem) else stem + 'ей'

    if form_type == 'soft':
        if low.endswith('ому'): return low[:-3] + 'ой'
        if low.endswith('ему'): return low[:-3] + 'ей'
        if low.endswith('ом'): return low[:-2] + 'ой'
        if low.endswith('ем') or low.endswith('ём'): return low[:-2] + 'ей'

    if form_type == 'direct':
        if low.endswith('ый') or low.endswith('ой'): return low[:-2] + 'ая'
        if low.endswith('ий'): return low[:-2] + 'яя'
        if low.endswith('ое'): return low[:-2] + 'ая'
        if low.endswith('ее'): return low[:-2] + 'яя'
        if low.endswith('ого'): return low[:-3] + 'ую'
        if low.endswith('его'): return low[:-3] + 'юю'

    if form_type == 'instrumental_plural':
        if low.endswith('ыми'): return low[:-3] + 'ыми'
        if low.endswith('ими'): return low[:-3] + 'ими'

    return None


def _agreement_for_ost_form(source: str, form_type: str) -> Optional[str]:
    low = source.lower()

    maps = {
        'instrumental': AGREEMENT_INSTRUMENTAL,
        'soft': AGREEMENT_SOFT,
        'direct': AGREEMENT_DIRECT,
        'instrumental_plural': {},
        'dative_plural': {},
        'genitive_plural': {},
        'prepositional_plural': {},
    }

    form_map = maps.get(form_type, {})
    if low in form_map:
        return _keep_case(source, form_map[low])

    if form_type in ('instrumental', 'soft', 'direct'):
        result = _convert_adjective_to_feminine(source, form_type)
        if result:
            return _keep_case(source, result)

    return None


def _is_word_token(token: str) -> bool:
    return bool(re.fullmatch(r'[А-Яа-яЁё]+', token))


def _previous_word_index(tokens: List[str], index: int) -> int:
    for i in range(index - 1, -1, -1):
        if _is_word_token(tokens[i]):
            return i
        if not re.fullmatch(r'\s+', tokens[i]):
            return -1
    return -1


def translate_text(text: str, hard: bool = True) -> str:
    tokens: List[str] = re.findall(
        r'[А-Яа-яЁё]+|[A-Za-z]+|\d+|\s+|[^\sА-Яа-яЁёA-Za-z\d]+',
        text
    ) or []

    translated: List[str] = []
    for idx, token in enumerate(tokens):
        translated.append(_translate_word(token, idx, tokens, hard))

    # согласование
    for i in range(len(tokens)):
        if not _is_word_token(tokens[i]):
            continue
        form_type = _get_ost_form_type(translated[i])
        if not form_type:
            continue

        j = _previous_word_index(tokens, i)
        checked = 0
        while j != -1 and checked < 4:
            src_low = tokens[j].lower()
            if src_low in {'с','со','в','во','на','к','ко','у','от','до','для',
                           'из','за','под','над','перед','после','и','а','но','как','что'}:
                break

            fixed = _agreement_for_ost_form(tokens[j], form_type)
            if fixed:
                translated[j] = fixed
            elif not _looks_like_adjective(src_low) and src_low not in {
                'мой','моя','моё','мое','твой','твоя','твоё','твое',
                'свой','своя','своё','свое','ваш','ваша','наш','наша',
                'этот','эта','то','тот','та'
            }:
                break

            j = _previous_word_index(tokens, j)
            checked += 1

    return ''.join(translated)


def _translate_word(token: str, idx: int, tokens: List[str], hard: bool) -> str:
    if not _is_russian_word(token):
        return token

    lower = token.lower()

    # контекстные фразы
    prev_idx = _previous_word_index(tokens, idx)
    prev_prev_idx = _previous_word_index(tokens, prev_idx) if prev_idx != -1 else -1
    prev = tokens[prev_idx].lower() if prev_idx != -1 else ''
    prev_prev = tokens[prev_prev_idx].lower() if prev_prev_idx != -1 else ''

    ctx = _translate_contextual_phrase(lower, prev, prev_prev)
    if ctx:
        return _keep_case(token, ctx)

    # pattern exceptions
    pattern = _translate_by_pattern(lower)
    if pattern:
        return _keep_case(token, pattern)

    # dictionary
    if lower in DICTIONARY:
        return _keep_case(token, DICTIONARY[lower])

    # stop words
    if lower in STOP_WORDS:
        return token

    # verbs
    if _looks_like_verb(lower):
        return token

    # adjectives
    if _looks_like_adjective(lower):
        return token

    # word-type models
    models = [
        _translate_enyee_enie,
        _translate_mya_noun,
        _translate_ica_noun,
        _translate_cia_noun,
        _translate_alternating_feminine,
        _translate_ina_noun,
        _translate_eyka_noun,
        _translate_ov_genitive_plural,
        _translate_ami_instrumental_plural,
        _translate_nik_noun,
        _translate_soft_neuter_like_pole,
    ]

    for model in models:
        result = model(lower)
        if result and _should_translate_as_noun(lower, hard):
            return _keep_case(token, result)

    # case noun model
    prev_word = tokens[_previous_word_index(tokens, idx)].lower() if _previous_word_index(tokens, idx) != -1 else ''
    case_result = _translate_case_noun_to_nost(lower, prev_word)
    if case_result and _should_translate_as_noun(lower, hard):
        return _keep_case(token, case_result)

    # burmal prefix words
    if hard and lower in BURMAL_PREFIX_WORDS:
        return _keep_case(token, _burmalize_with_prefix(lower))

    if not _should_translate_as_noun(lower, hard):
        return token

    # default: -ость/-ность
    result = _add_ost_or_nost(lower)
    return _keep_case(token, result)
