from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse

import boto3
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    ApprovalStatus,
    Enrollment,
    Homework,
    HomeworkSubmission,
    Subject,
    TutorOfferPackage,
    TutorProfile,
    TutorReview,
    User,
    UserRole,
)


@dataclass(frozen=True)
class SeedUser:
    email: str
    full_name: str
    role: UserRole
    avatar_key: str
    color: str
    accent: str = "#ffffff"
    subject: Subject | None = None
    price_rub: int | None = None
    description: str | None = None
    bio: str | None = None
    education: str | None = None
    experience: str | None = None
    lesson_format: str | None = None


@dataclass(frozen=True)
class SeedHomework:
    tutor_email: str
    title: str
    description: str
    target_student_email: str | None = None
    attachment_file_key: str | None = None
    attachment_file_name: str | None = None
    attachment_content_type: str | None = None


@dataclass(frozen=True)
class SeedOfferPackage:
    tutor_email: str
    title: str
    subject: Subject
    price_rub: int
    description: str


@dataclass(frozen=True)
class SeedHomeworkSubmission:
    student_email: str
    tutor_email: str
    homework_title: str
    grade: int
    teacher_comment: str | None = None


SEED_USERS = [
    SeedUser(
        email="egorburakov11@yandex.ru",
        full_name="Егор Бураков",
        role=UserRole.tutor,
        avatar_key="avatars/seed/egor-burakov-tutor.svg",
        color="#9ac7f7",
        accent="#eef6ff",
        subject=Subject.math,
        price_rub=6500,
        description="Подготовка к ЕГЭ по математике с упором на спокойный темп, аккуратное оформление и понятные разборы.",
        bio="Помогаю уверенно пройти темы ЕГЭ без перегруза: разбираем задачи по шагам, держим темп и не теряем логику решения.",
        education="МГТУ им. Баумана, прикладная математика.",
        experience="4 года индивидуальной подготовки школьников к профильной математике.",
        lesson_format="Онлайн, домашние задания после каждого занятия, разбор ошибок и постоянная связь в чате.",
    ),
    SeedUser(
        email="egorburakov4@yandex.ru",
        full_name="Егор Бураков",
        role=UserRole.student,
        avatar_key="avatars/seed/egor-burakov-student.svg",
        color="#f6c8d4",
        accent="#fff1f5",
    ),
    SeedUser(
        email="alina.math@example.com",
        full_name="Алина Воронцова",
        role=UserRole.tutor,
        avatar_key="avatars/seed/alina-vorontsova.svg",
        color="#7ac7b6",
        accent="#dff7f1",
        subject=Subject.math,
        price_rub=6800,
        description="Готовлю к ЕГЭ по математике, разбираю сложные задачи второй части.",
        bio="8 лет готовлю к профильной математике. Люблю понятные схемы, регулярные мини-пробники и спокойный темп.",
        education="МГУ, факультет вычислительной математики и кибернетики.",
        experience="8 лет индивидуальной подготовки, более 120 учеников.",
        lesson_format="Онлайн 2 раза в неделю, домашние задания, пробники и личный чат.",
    ),
    SeedUser(
        email="max.rus@example.com",
        full_name="Максим Беляев",
        role=UserRole.tutor,
        avatar_key="avatars/seed/maksim-belyaev.svg",
        color="#f0b27a",
        accent="#fff0de",
        subject=Subject.russian,
        price_rub=5900,
        description="Русский язык без зубрежки: сочинения, тесты и системная практика.",
        bio="Помогаю поднять результат по русскому языку за счет структуры, регулярных разборов и понятных шаблонов.",
        education="РГГУ, филологический факультет.",
        experience="6 лет подготовки к ЕГЭ и олимпиадным сочинениям.",
        lesson_format="Онлайн, разбор сочинений в документах и персональные комментарии.",
    ),
    SeedUser(
        email="sofia.bio@example.com",
        full_name="София Климова",
        role=UserRole.tutor,
        avatar_key="avatars/seed/sofia-klimova.svg",
        color="#a8d08d",
        accent="#eff8e5",
        subject=Subject.biology,
        price_rub=7200,
        description="Биология для ЕГЭ: теория, схемы и практика на реальных вариантах.",
        bio="Делаю сложные темы по биологии визуальными и понятными. Хорошо подхожу тем, кто любит системность.",
        education="Первый МГМУ им. Сеченова, лечебное дело.",
        experience="5 лет подготовки школьников к биологии и медицинским вузам.",
        lesson_format="Видеоуроки, схемы, опросы и короткие еженедельные тесты.",
    ),
    SeedUser(
        email="nikita.inf@example.com",
        full_name="Никита Сергеев",
        role=UserRole.tutor,
        avatar_key="avatars/seed/nikita-sergeev.svg",
        color="#8ea9db",
        accent="#e8efff",
        subject=Subject.informatics,
        price_rub=7500,
        description="Информатика ЕГЭ: задачи на программирование, алгоритмы и аккуратная практика.",
        bio="Объясняю информатику через логику и код, чтобы ученик не угадывал, а понимал ход решения.",
        education="ИТМО, программная инженерия.",
        experience="7 лет веду информатику, Python и алгоритмы.",
        lesson_format="Онлайн с демонстрацией кода, разбором ДЗ и тренировкой задач ЕГЭ.",
    ),
    SeedUser(
        email="ksenia.chem@example.com",
        full_name="Ксения Лаврова",
        role=UserRole.tutor,
        avatar_key="avatars/seed/kseniya-lavrova.svg",
        color="#d7b8ff",
        accent="#f4e9ff",
        subject=Subject.chemistry,
        price_rub=6400,
        description="Химия ЕГЭ без провалов в задачах: теория, цепочки превращений и много понятной практики.",
        bio="Спокойно раскладываю химию по блокам, чтобы ученик видел логику реакций, а не заучивал их вслепую.",
        education="РХТУ им. Менделеева, химическая технология.",
        experience="6 лет подготовки к ЕГЭ и вступительным экзаменам по химии.",
        lesson_format="Онлайн, рабочая тетрадь с конспектами, домашка после каждого занятия и разбор ошибок в чате.",
    ),
    SeedUser(
        email="denis.phys@example.com",
        full_name="Денис Чернов",
        role=UserRole.tutor,
        avatar_key="avatars/seed/denis-chernov.svg",
        color="#8fd3d7",
        accent="#e7fbfd",
        subject=Subject.physics,
        price_rub=7100,
        description="Физика ЕГЭ: от базовой механики до электричества, с акцентом на понимание, а не на зубрежку.",
        bio="Помогаю собрать крепкую базу по формулам и научиться уверенно решать вторую часть.",
        education="МФТИ, прикладная физика и математика.",
        experience="7 лет веду подготовку к ЕГЭ и олимпиадам по физике.",
        lesson_format="Онлайн с планшетом, подборка задач по темам, еженедельные мини-срезы.",
    ),
    SeedUser(
        email="maria.eng@example.com",
        full_name="Мария Соколова",
        role=UserRole.tutor,
        avatar_key="avatars/seed/maria-sokolova.svg",
        color="#ffbf9b",
        accent="#fff0e7",
        subject=Subject.english,
        price_rub=6100,
        description="Английский для ЕГЭ: письмо, эссе, аудирование и говорение в одном понятном маршруте.",
        bio="Люблю, когда ученик говорит и пишет уверенно, поэтому много внимания уделяю практике и шаблонам.",
        education="МГЛУ, перевод и переводоведение.",
        experience="5 лет работы с подростками и подготовкой к ЕГЭ по английскому.",
        lesson_format="Онлайн, разговорные разминки, проверка письменных работ и голосовые комментарии.",
    ),
    SeedUser(
        email="oleg.hist@example.com",
        full_name="Олег Журавлев",
        role=UserRole.tutor,
        avatar_key="avatars/seed/oleg-zhuravlev.svg",
        color="#c7d59f",
        accent="#f0f6df",
        subject=Subject.history,
        price_rub=5600,
        description="История ЕГЭ: даты, причины, следствия и аргументы без хаоса в голове.",
        bio="Собираю историю в цельную картину через ленты времени, схемы и короткие повторения.",
        education="СПбГУ, исторический факультет.",
        experience="6 лет подготовки к ЕГЭ по истории и обществознанию.",
        lesson_format="Онлайн-уроки, карточки дат, еженедельное повторение и устные зачеты.",
    ),
    SeedUser(
        email="polina.student@example.com",
        full_name="Полина Миронова",
        role=UserRole.student,
        avatar_key="avatars/seed/polina-mironova.svg",
        color="#f4cccc",
        accent="#fff2f2",
    ),
    SeedUser(
        email="ivan.student@example.com",
        full_name="Иван Лобанов",
        role=UserRole.student,
        avatar_key="avatars/seed/ivan-lobanov.svg",
        color="#c9daf8",
        accent="#eef4ff",
    ),
    SeedUser(
        email="liza.student@example.com",
        full_name="Елизавета Орлова",
        role=UserRole.student,
        avatar_key="avatars/seed/elizaveta-orlova.svg",
        color="#d9ead3",
        accent="#f3fbf0",
    ),
    SeedUser(
        email="artem.student@example.com",
        full_name="Артем Громов",
        role=UserRole.student,
        avatar_key="avatars/seed/artem-gromov.svg",
        color="#ead1dc",
        accent="#fff1f7",
    ),
    SeedUser(
        email="vera.student@example.com",
        full_name="Вера Крылова",
        role=UserRole.student,
        avatar_key="avatars/seed/vera-krylova.svg",
        color="#ffd7e6",
        accent="#fff3f8",
    ),
    SeedUser(
        email="kirill.student@example.com",
        full_name="Кирилл Демин",
        role=UserRole.student,
        avatar_key="avatars/seed/kirill-demin.svg",
        color="#d2e6ff",
        accent="#f1f8ff",
    ),
    SeedUser(
        email="mila.student@example.com",
        full_name="Мила Трофимова",
        role=UserRole.student,
        avatar_key="avatars/seed/mila-trofimova.svg",
        color="#d9f0c7",
        accent="#f5fde9",
    ),
    SeedUser(
        email="roman.student@example.com",
        full_name="Роман Елисеев",
        role=UserRole.student,
        avatar_key="avatars/seed/roman-eliseev.svg",
        color="#f4dfb8",
        accent="#fff6e7",
    ),
    SeedUser(
        email="daria.student@example.com",
        full_name="Дарья Нестерова",
        role=UserRole.student,
        avatar_key="avatars/seed/daria-nesterova.svg",
        color="#e9d5ff",
        accent="#f8efff",
    ),
    SeedUser(
        email="nikolai.student@example.com",
        full_name="Николай Самойлов",
        role=UserRole.student,
        avatar_key="avatars/seed/nikolai-samoylov.svg",
        color="#d0e6a5",
        accent="#f4fbe6",
    ),
    SeedUser(
        email="anastasia.student@example.com",
        full_name="Анастасия Федорова",
        role=UserRole.student,
        avatar_key="avatars/seed/anastasia-fedorova.svg",
        color="#ffd6cc",
        accent="#fff1ec",
    ),
    SeedUser(
        email="timur.student@example.com",
        full_name="Тимур Абрамов",
        role=UserRole.student,
        avatar_key="avatars/seed/timur-abramov.svg",
        color="#cfe2f3",
        accent="#eef6ff",
    ),
    SeedUser(
        email="yaroslava.student@example.com",
        full_name="Ярослава Егорова",
        role=UserRole.student,
        avatar_key="avatars/seed/yaroslava-egorova.svg",
        color="#fce5cd",
        accent="#fff6ea",
    ),
    SeedUser(
        email="stepan.student@example.com",
        full_name="Степан Козлов",
        role=UserRole.student,
        avatar_key="avatars/seed/stepan-kozlov.svg",
        color="#d9ead3",
        accent="#f4fbf1",
    ),
    SeedUser(
        email="ksenia.student@example.com",
        full_name="Ксения Романова",
        role=UserRole.student,
        avatar_key="avatars/seed/kseniya-romanova-student.svg",
        color="#ead1dc",
        accent="#fdf2f7",
    ),
    SeedUser(
        email="gleb.student@example.com",
        full_name="Глеб Никонов",
        role=UserRole.student,
        avatar_key="avatars/seed/gleb-nikonov.svg",
        color="#d0d9ff",
        accent="#eef1ff",
    ),
    SeedUser(
        email="uliana.student@example.com",
        full_name="Ульяна Белова",
        role=UserRole.student,
        avatar_key="avatars/seed/uliana-belova.svg",
        color="#f4cccc",
        accent="#fff2f2",
    ),
    SeedUser(
        email="egor.student@example.com",
        full_name="Егор Дроздов",
        role=UserRole.student,
        avatar_key="avatars/seed/egor-drozdov.svg",
        color="#c9daf8",
        accent="#eef5ff",
    ),
]


SEED_REVIEWS = [
    ("polina.student@example.com", "alina.math@example.com", 5, "Очень понятные объяснения и сильная практика перед пробниками."),
    ("ivan.student@example.com", "alina.math@example.com", 4, "Стало проще решать вторую часть, особенно параметры."),
    ("liza.student@example.com", "max.rus@example.com", 5, "Сочинение перестало пугать, появилась структура и уверенность."),
    ("artem.student@example.com", "sofia.bio@example.com", 5, "Классные схемы и конспекты, теория запоминается намного легче."),
    ("polina.student@example.com", "nikita.inf@example.com", 4, "Хорошо объясняет задачи на программирование и логику."),
    ("vera.student@example.com", "ksenia.chem@example.com", 5, "Очень четко объясняет реакции и помогает не путаться в цепочках. После пары занятий стало намного спокойнее."),
    ("roman.student@example.com", "ksenia.chem@example.com", 4, "Понравилось, что много практики и все ошибки разбираются сразу после домашней работы."),
    ("kirill.student@example.com", "denis.phys@example.com", 5, "Наконец понял механику и перестал бояться задач со второй части. Объяснения очень логичные."),
    ("mila.student@example.com", "denis.phys@example.com", 5, "Сильный преподаватель, хорошо держит темп и дает нормальные домашние задания без перегруза."),
    ("ivan.student@example.com", "maria.eng@example.com", 5, "Стало гораздо легче писать эссе и письмо, появились хорошие шаблоны и уверенность."),
    ("polina.student@example.com", "maria.eng@example.com", 4, "Классные разговорные разминки и понятные комментарии к письменным работам."),
    ("artem.student@example.com", "oleg.hist@example.com", 5, "История наконец сложилась в систему, а не в набор случайных дат. Очень помогают схемы."),
    ("liza.student@example.com", "oleg.hist@example.com", 4, "Нравится, что материал повторяется блоками и не вываливается все сразу."),
]


SEED_HOMEWORK = [
    SeedHomework(
        "egorburakov11@yandex.ru",
        "Параметры: базовый разбор",
        "Решите 6 задач с параметром и коротко подпишите ход рассуждений под каждым номером.",
        target_student_email="egorburakov4@yandex.ru",
        attachment_file_key="homework/seed/egor-params.pdf",
        attachment_file_name="egor-params.pdf",
        attachment_content_type="application/pdf",
    ),
    SeedHomework(
        "egorburakov11@yandex.ru",
        "Графики и производная",
        "Посмотрите фото задания, решите номера на анализ графика и оформите ответы одним файлом.",
        attachment_file_key="homework/seed/egor-graph.svg",
        attachment_file_name="egor-graph.svg",
        attachment_content_type="image/svg+xml",
    ),
    SeedHomework(
        "alina.math@example.com",
        "Параметры и неравенства",
        "Разберите 8 задач второй части и оформите полные решения.",
        attachment_file_key="homework/seed/alina-params.pdf",
        attachment_file_name="alina-params.pdf",
        attachment_content_type="application/pdf",
    ),
    SeedHomework(
        "alina.math@example.com",
        "Тригонометрия ЕГЭ",
        "Решите вариант по тригонометрии и добавьте пояснения к сложным номерам.",
        attachment_file_key="homework/seed/alina-trigonometry.svg",
        attachment_file_name="alina-trigonometry.svg",
        attachment_content_type="image/svg+xml",
    ),
    SeedHomework("max.rus@example.com", "Сочинение ЕГЭ", "Напишите сочинение по тексту и выделите авторскую позицию."),
    SeedHomework("max.rus@example.com", "Тестовая часть по орфографии", "Выполните подборку заданий на орфографию и пунктуацию."),
    SeedHomework("sofia.bio@example.com", "Генетика и клетка", "Решите задачи по генетике и повторите строение клетки."),
    SeedHomework("nikita.inf@example.com", "Алгоритмы и Python", "Напишите решения пяти задач на циклы, массивы и строки."),
    SeedHomework("ksenia.chem@example.com", "Цепочки превращений", "Составьте уравнения реакций и объясните выбор коэффициентов."),
    SeedHomework("denis.phys@example.com", "Механика", "Решите задачи на законы Ньютона и сохранение энергии."),
    SeedHomework("maria.eng@example.com", "Essay + Email", "Подготовьте письмо и эссе по шаблону ЕГЭ."),
    SeedHomework("oleg.hist@example.com", "Историческое сочинение", "Напишите развернутый ответ по историческому периоду."),
]


SEED_OFFER_PACKAGES = [
    SeedOfferPackage(
        "egorburakov11@yandex.ru",
        "Интенсив перед ЕГЭ",
        Subject.math,
        4200,
        "Быстрый формат на 2 недели: разбор сложных задач, мини-пробники и ежедневная связь по домашке.",
    ),
    SeedOfferPackage(
        "egorburakov11@yandex.ru",
        "Поддерживающий формат",
        Subject.math,
        2800,
        "Спокойный темп с одним занятием в неделю, домашними заданиями и короткими видеоразборами.",
    ),
    SeedOfferPackage(
        "alina.math@example.com",
        "Разбор пробников",
        Subject.math,
        3500,
        "Отдельный формат под пробники: проверка работы, разбор ошибок и план следующего шага.",
    ),
]


SEED_HOMEWORK_SUBMISSIONS = [
    SeedHomeworkSubmission(
        "egorburakov4@yandex.ru",
        "egorburakov11@yandex.ru",
        "Параметры: базовый разбор",
        5,
        "Очень аккуратное решение. Особенно хорошо оформлен разбор последнего номера.",
    ),
    SeedHomeworkSubmission(
        "egorburakov4@yandex.ru",
        "egorburakov11@yandex.ru",
        "Графики и производная",
        4,
        "Ход решения верный, но в двух пунктах стоит чуть подробнее подписывать выводы по графику.",
    ),
    SeedHomeworkSubmission("polina.student@example.com", "alina.math@example.com", "Параметры и неравенства", 5),
    SeedHomeworkSubmission("polina.student@example.com", "alina.math@example.com", "Тригонометрия ЕГЭ", 5),
    SeedHomeworkSubmission("polina.student@example.com", "maria.eng@example.com", "Essay + Email", 5),
    SeedHomeworkSubmission("ivan.student@example.com", "alina.math@example.com", "Параметры и неравенства", 5),
    SeedHomeworkSubmission("ivan.student@example.com", "maria.eng@example.com", "Essay + Email", 4),
    SeedHomeworkSubmission("liza.student@example.com", "max.rus@example.com", "Сочинение ЕГЭ", 5),
    SeedHomeworkSubmission("liza.student@example.com", "max.rus@example.com", "Тестовая часть по орфографии", 5),
    SeedHomeworkSubmission("liza.student@example.com", "oleg.hist@example.com", "Историческое сочинение", 4),
    SeedHomeworkSubmission("artem.student@example.com", "sofia.bio@example.com", "Генетика и клетка", 5),
    SeedHomeworkSubmission("artem.student@example.com", "oleg.hist@example.com", "Историческое сочинение", 5),
    SeedHomeworkSubmission("vera.student@example.com", "ksenia.chem@example.com", "Цепочки превращений", 5),
    SeedHomeworkSubmission("vera.student@example.com", "denis.phys@example.com", "Механика", 5),
    SeedHomeworkSubmission("kirill.student@example.com", "denis.phys@example.com", "Механика", 5),
    SeedHomeworkSubmission("mila.student@example.com", "denis.phys@example.com", "Механика", 5),
    SeedHomeworkSubmission("roman.student@example.com", "ksenia.chem@example.com", "Цепочки превращений", 4),
    SeedHomeworkSubmission("daria.student@example.com", "max.rus@example.com", "Сочинение ЕГЭ", 5),
    SeedHomeworkSubmission("daria.student@example.com", "max.rus@example.com", "Тестовая часть по орфографии", 5),
    SeedHomeworkSubmission("nikolai.student@example.com", "nikita.inf@example.com", "Алгоритмы и Python", 5),
    SeedHomeworkSubmission("anastasia.student@example.com", "sofia.bio@example.com", "Генетика и клетка", 4),
    SeedHomeworkSubmission("timur.student@example.com", "nikita.inf@example.com", "Алгоритмы и Python", 5),
    SeedHomeworkSubmission("yaroslava.student@example.com", "maria.eng@example.com", "Essay + Email", 5),
    SeedHomeworkSubmission("stepan.student@example.com", "oleg.hist@example.com", "Историческое сочинение", 5),
    SeedHomeworkSubmission("ksenia.student@example.com", "max.rus@example.com", "Сочинение ЕГЭ", 4),
    SeedHomeworkSubmission("gleb.student@example.com", "nikita.inf@example.com", "Алгоритмы и Python", 4),
    SeedHomeworkSubmission("uliana.student@example.com", "maria.eng@example.com", "Essay + Email", 5),
    SeedHomeworkSubmission("egor.student@example.com", "alina.math@example.com", "Тригонометрия ЕГЭ", 5),
]


def _s3_client():
    endpoint_url = settings.s3_endpoint_url
    if endpoint_url:
        parsed = urlparse(endpoint_url)
        if parsed.hostname in {"localhost", "127.0.0.1"}:
            netloc = parsed.netloc.replace(parsed.hostname, "minio")
            endpoint_url = urlunparse(parsed._replace(netloc=netloc))
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )


def _avatar_svg(name: str, color: str, accent: str) -> str:
    initials = "".join(part[:1].upper() for part in name.split()[:2]) or "U"
    variant = sum(ord(char) for char in name) % 4
    decorations = [
        f'<circle cx="128" cy="34" r="18" fill="{accent}" opacity="0.95"/><circle cx="28" cy="130" r="22" fill="rgba(255,255,255,0.24)"/>',
        f'<rect x="18" y="18" width="42" height="42" rx="14" fill="{accent}" opacity="0.9"/><rect x="106" y="104" width="34" height="34" rx="10" fill="rgba(255,255,255,0.22)"/>',
        f'<path d="M0 122 C38 96 72 144 112 118 C132 104 144 92 160 96 V160 H0 Z" fill="{accent}" opacity="0.9"/><circle cx="118" cy="40" r="14" fill="rgba(255,255,255,0.22)"/>',
        f'<path d="M20 24 L140 24 L140 42 L20 42 Z" fill="{accent}" opacity="0.85"/><path d="M24 118 L96 118 L96 136 L24 136 Z" fill="rgba(255,255,255,0.22)"/>',
    ][variant]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
  <rect width="160" height="160" rx="28" fill="{color}"/>
  {decorations}
  <circle cx="80" cy="62" r="28" fill="rgba(255,255,255,0.30)"/>
  <text x="80" y="106" text-anchor="middle" font-family="Arial, sans-serif" font-size="42" font-weight="700" fill="#243041">{initials}</text>
</svg>'''


def _sample_homework_pdf(title: str) -> bytes:
    title_ascii = title.encode("cp1251", errors="replace").decode("latin-1")
    stream = (
        "BT\n"
        "/F1 18 Tf\n"
        "72 770 Td\n"
        f"({title_ascii}) Tj\n"
        "0 -28 Td\n"
        "/F1 12 Tf\n"
        "(1. Solve all tasks carefully and show each step.) Tj\n"
        "0 -20 Td\n"
        "(2. Highlight the final answer in each problem.) Tj\n"
        "0 -20 Td\n"
        "(3. Upload your solution as PDF or image.) Tj\n"
        "ET"
    )
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        f"4 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "0000000010 00000 n \n0000000063 00000 n \n0000000122 00000 n \n"
        "0000000248 00000 n \n0000000000 00000 n \n"
        "trailer << /Root 1 0 R /Size 6 >>\nstartxref\n0\n%%EOF"
    )
    return pdf.encode("latin-1")


def _sample_homework_image(title: str) -> bytes:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
  <rect width="1200" height="1600" fill="#f7fbff"/>
  <rect x="70" y="70" width="1060" height="1460" rx="42" fill="#ffffff" stroke="#cfd8e6" stroke-width="6"/>
  <text x="110" y="190" font-family="Arial, sans-serif" font-size="54" font-weight="700" fill="#223047">{safe_title}</text>
  <text x="110" y="270" font-family="Arial, sans-serif" font-size="28" fill="#506079">Фото задания для просмотра в личном кабинете</text>
  <line x1="110" y1="340" x2="1090" y2="340" stroke="#d7e3ef" stroke-width="4"/>
  <text x="110" y="430" font-family="Arial, sans-serif" font-size="30" fill="#2b3a52">1. Решите задачи 13 и 15 из варианта.</text>
  <text x="110" y="510" font-family="Arial, sans-serif" font-size="30" fill="#2b3a52">2. Подпишите каждый шаг решения.</text>
  <text x="110" y="590" font-family="Arial, sans-serif" font-size="30" fill="#2b3a52">3. Отправьте ответ одним файлом.</text>
  <rect x="110" y="700" width="420" height="260" rx="26" fill="#e7f3ef"/>
  <text x="150" y="790" font-family="Arial, sans-serif" font-size="34" font-weight="700" fill="#2a6c61">Профильная математика</text>
  <text x="150" y="860" font-family="Arial, sans-serif" font-size="28" fill="#37516d">Акцент на аккуратное оформление</text>
  <text x="150" y="930" font-family="Arial, sans-serif" font-size="28" fill="#37516d">и проверку каждого ответа.</text>
</svg>'''.encode("utf-8")


def seed_demo_data(db: Session) -> None:
    s3 = _s3_client()
    bucket = settings.s3_bucket
    users_by_email: dict[str, User] = {}

    for seed_user in SEED_USERS:
        user = db.query(User).filter(User.email == seed_user.email).first()
        if not user:
            user = User(
                role=seed_user.role,
                email=seed_user.email,
                full_name=seed_user.full_name,
                avatar_file_key=seed_user.avatar_key,
                password_hash=hash_password("TestPass123!"),
                approval_status=ApprovalStatus.approved,
                email_verified=True,
                kyc_verified=seed_user.role == UserRole.tutor,
                email_code=None,
            )
            db.add(user)
            db.flush()
        else:
            user.avatar_file_key = seed_user.avatar_key
            user.approval_status = ApprovalStatus.approved
            user.email_verified = True
            if seed_user.role == UserRole.tutor:
                user.kyc_verified = True

        s3.put_object(
            Bucket=bucket,
            Key=seed_user.avatar_key,
            Body=_avatar_svg(seed_user.full_name, seed_user.color, seed_user.accent).encode("utf-8"),
            ContentType="image/svg+xml",
        )

        if seed_user.role == UserRole.tutor:
            profile = db.query(TutorProfile).filter(TutorProfile.user_id == user.id).first()
            if not profile:
                profile = TutorProfile(user_id=user.id)
                db.add(profile)
            profile.subject = seed_user.subject
            profile.price_rub = seed_user.price_rub
            profile.description = seed_user.description
            profile.bio = seed_user.bio
            profile.education = seed_user.education
            profile.experience = seed_user.experience
            profile.lesson_format = seed_user.lesson_format
            profile.offer_published = True

        users_by_email[seed_user.email] = user

    db.flush()

    for student_email, tutor_email, stars, text in SEED_REVIEWS:
        student = users_by_email[student_email]
        tutor = users_by_email[tutor_email]

        enrollment = db.query(Enrollment).filter_by(student_id=student.id, tutor_id=tutor.id).first()
        if not enrollment:
            db.add(Enrollment(student_id=student.id, tutor_id=tutor.id))

        review = db.query(TutorReview).filter_by(student_id=student.id, tutor_id=tutor.id).first()
        if not review:
            db.add(TutorReview(student_id=student.id, tutor_id=tutor.id, stars=stars, text=text))
        else:
            review.stars = stars
            review.text = text

    db.flush()

    for seed_package in SEED_OFFER_PACKAGES:
        tutor = users_by_email[seed_package.tutor_email]
        package = (
            db.query(TutorOfferPackage)
            .filter(TutorOfferPackage.tutor_id == tutor.id, TutorOfferPackage.title == seed_package.title)
            .first()
        )
        if not package:
            package = TutorOfferPackage(
                tutor_id=tutor.id,
                title=seed_package.title,
                subject=seed_package.subject,
                price_rub=seed_package.price_rub,
                description=seed_package.description,
                is_active=True,
            )
            db.add(package)
        else:
            package.subject = seed_package.subject
            package.price_rub = seed_package.price_rub
            package.description = seed_package.description
            package.is_active = True

    db.flush()

    homeworks_by_key: dict[tuple[str, str], Homework] = {}
    base_time = datetime.utcnow() - timedelta(days=14)

    for index, seed_homework in enumerate(SEED_HOMEWORK):
        tutor = users_by_email[seed_homework.tutor_email]
        homework = (
            db.query(Homework)
            .filter(Homework.tutor_id == tutor.id, Homework.title == seed_homework.title)
            .first()
        )
        if not homework:
            target_student_id = None
            if seed_homework.target_student_email:
                target_student_id = users_by_email[seed_homework.target_student_email].id
            homework = Homework(
                tutor_id=tutor.id,
                target_student_id=target_student_id,
                title=seed_homework.title,
                description=seed_homework.description,
                attachment_file_key=seed_homework.attachment_file_key,
                attachment_file_name=seed_homework.attachment_file_name,
                created_at=base_time + timedelta(days=index),
            )
            db.add(homework)
            db.flush()
        else:
            homework.target_student_id = (
                users_by_email[seed_homework.target_student_email].id if seed_homework.target_student_email else None
            )
            homework.description = seed_homework.description
            homework.attachment_file_key = seed_homework.attachment_file_key
            homework.attachment_file_name = seed_homework.attachment_file_name

        if seed_homework.attachment_file_key and seed_homework.attachment_file_name and seed_homework.attachment_content_type:
            body = (
                _sample_homework_pdf(seed_homework.title)
                if seed_homework.attachment_content_type == "application/pdf"
                else _sample_homework_image(seed_homework.title)
            )
            s3.put_object(
                Bucket=bucket,
                Key=seed_homework.attachment_file_key,
                Body=body,
                ContentType=seed_homework.attachment_content_type,
            )

        homeworks_by_key[(seed_homework.tutor_email, seed_homework.title)] = homework

    db.flush()

    for index, seed_submission in enumerate(SEED_HOMEWORK_SUBMISSIONS):
        student = users_by_email[seed_submission.student_email]
        tutor = users_by_email[seed_submission.tutor_email]
        homework = homeworks_by_key[(seed_submission.tutor_email, seed_submission.homework_title)]

        enrollment = db.query(Enrollment).filter_by(student_id=student.id, tutor_id=tutor.id).first()
        if not enrollment:
            db.add(Enrollment(student_id=student.id, tutor_id=tutor.id))
            db.flush()

        submission = (
            db.query(HomeworkSubmission)
            .filter_by(homework_id=homework.id, student_id=student.id)
            .first()
        )
        if not submission:
            submission = HomeworkSubmission(
                homework_id=homework.id,
                student_id=student.id,
                file_key=f"homework/seed/{student.id}-{homework.id}.pdf",
                file_name=f"answer-{homework.id}.pdf",
                grade=seed_submission.grade,
                teacher_comment=seed_submission.teacher_comment,
                created_at=base_time + timedelta(days=index, hours=6),
            )
            db.add(submission)
        else:
            submission.file_key = f"homework/seed/{student.id}-{homework.id}.pdf"
            submission.file_name = f"answer-{homework.id}.pdf"
            submission.grade = seed_submission.grade
            submission.teacher_comment = seed_submission.teacher_comment

        s3.put_object(
            Bucket=bucket,
            Key=f"homework/seed/{student.id}-{homework.id}.pdf",
            Body=_sample_homework_pdf(f"Ответ: {homework.title}"),
            ContentType="application/pdf",
        )

    db.commit()
