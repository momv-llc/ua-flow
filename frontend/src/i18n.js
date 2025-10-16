import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

const resources = {
  ua: {
    translation: {
      brand: {
        tagline: 'Українська платформа управління продуктом',
      },
      language: {
        label: 'Мова',
        ua: 'Українська',
        en: 'English',
        ru: 'Русский',
      },
      theme: {
        light: 'Світла тема',
        dark: 'Темна тема',
        toggle: 'Перемкнути тему',
      },
      nav: {
        platform: 'Платформа',
        management: 'Управління',
        admin: 'Адміністрування',
        dashboard: 'Дашборд',
        tasks: 'Задачі',
        docs: 'Документи',
        support: 'Підтримка',
        integrations: 'Integration Hub',
        analytics: 'Аналітика',
        settings: 'Налаштування',
        marketplace: 'Маркетплейс',
        users: 'Користувачі та ролі',
        audit: 'Аудит і безпека',
      },
      topbar: {
        welcome: 'Вітаємо, {{name}}!',
        description:
          'Єдина панель контролю проектів, документів, служби підтримки та інтеграцій.',
        logout: 'Вийти',
      },
      dashboard: {
        modulesHeading: 'Вітрина модулів',
        modulesDescription:
          'Ознайомтеся з тим, як UA FLOW поєднує класичні підходи Atlassian з українською специфікою.',
        cards: {
          kanban: {
            title: 'Kanban-дошка',
            description: 'Відстеження стану задач у режимі реального часу та контроль WIP-лімітів.',
            cardsLabel: 'карток',
          },
          scrum: {
            title: 'Scrum-спринт',
            description: 'Плануйте спринти, фіксуйте velocity команди та автоматично генеруйте звіти.',
          },
          docs: {
            title: 'Документація',
            description: 'Wiki-сторінки, версіонування та КЕП-підписання документів.',
            signed: 'КЕП підтверджено',
            pending: 'Очікує підпис',
            version: 'Версія {{value}}',
          },
          support: {
            title: 'Тікети підтримки',
            description: 'SLA, маршрутизація та чат з клієнтом через веб-інтерфейс або Telegram.',
          },
        },
        stats: {
          activeTasks: 'Активних задач',
          activeTrend: 'за тиждень',
          sla: 'Середній SLA (год)',
          slaTrend: 'швидше, ніж раніше',
          docsSigned: 'Документів підписано',
          docsTrend: 'підписів',
        },
        projects: {
          title: 'Проєкти та спринти',
          empty: 'У вас поки немає проєктів',
          methodology: 'Методологія',
          key: 'Ключ',
        },
        focus: {
          title: 'Фокусні задачі',
          columns: {
            id: 'ID',
            title: 'Назва',
            status: 'Статус',
            assignee: 'Виконавець',
            due: 'Дедлайн',
          },
          empty: 'Призначені задачі не знайдено',
        },
      },
      integrations: {
        title: 'Активні інтеграції',
        count: '{{count}} підключень',
        lastSync: 'Останній обмін',
        test: 'Перевірити з’єднання',
        sync: 'Черга синхронізації',
        logs: 'Логи',
        payloadLabel: 'Payload (JSON)',
        sandboxTitle: 'Пісочниці',
        sandboxRun: 'Запустити пісочницю',
        queueStatus: 'Статус черги',
        queued: 'Задача додана до черги',
        eager: 'Черга виконується локально (режим eager).',
        resultTitle: 'Результат',
        noIntegrations: 'Інтеграції ще не налаштовані',
        noLogs: 'Логи з’являться після синхронізації',
        sandboxNote: 'Використовуйте пісочниці для локальної перевірки без зовнішніх API.',
      },
      auth: {
        loginTitle: 'Вхід',
        registerTitle: 'Реєстрація',
        email: 'Email',
        password: 'Пароль',
        submit: 'Продовжити',
        haveAccount: 'Вже є акаунт?',
        noAccount: 'Ще не маєте акаунта?',
        goLogin: 'Увійти',
        goRegister: 'Зареєструватися',
        registerSuccess: 'Акаунт створено! Перенаправляємо на вхід…',
      },
      common: {
        loading: 'Завантаження…',
        retry: 'Спробувати ще раз',
      },
    },
  },
  en: {
    translation: {
      brand: {
        tagline: 'Ukrainian product operations platform',
      },
      language: {
        label: 'Language',
        ua: 'Українська',
        en: 'English',
        ru: 'Русский',
      },
      theme: {
        light: 'Light theme',
        dark: 'Dark theme',
        toggle: 'Toggle theme',
      },
      nav: {
        platform: 'Platform',
        management: 'Management',
        admin: 'Administration',
        dashboard: 'Dashboard',
        tasks: 'Tasks',
        docs: 'Docs',
        support: 'Support',
        integrations: 'Integration Hub',
        analytics: 'Analytics',
        settings: 'Settings',
        marketplace: 'Marketplace',
        users: 'Users & Roles',
        audit: 'Audit & Security',
      },
      topbar: {
        welcome: 'Welcome, {{name}}!',
        description:
          'A single control plane for tasks, documentation, the service desk, and integrations.',
        logout: 'Sign out',
      },
      dashboard: {
        modulesHeading: 'Module showcase',
        modulesDescription:
          'See how UA FLOW blends Atlassian practices with Ukrainian compliance out of the box.',
        cards: {
          kanban: {
            title: 'Kanban board',
            description: 'Track work-in-progress limits and throughput in real time.',
            cardsLabel: 'cards',
          },
          scrum: {
            title: 'Scrum sprint',
            description: 'Plan sprints, measure team velocity, and surface burndown trends automatically.',
          },
          docs: {
            title: 'Documentation',
            description: 'Collaborative wiki pages with version history and qualified e-signatures.',
            signed: 'Signed with QES',
            pending: 'Awaiting signature',
            version: 'Version {{value}}',
          },
          support: {
            title: 'Support tickets',
            description: 'SLA-aware routing with omnichannel chat via web or Telegram.',
          },
        },
        stats: {
          activeTasks: 'Active tasks',
          activeTrend: 'vs last week',
          sla: 'Average SLA (hrs)',
          slaTrend: 'faster than baseline',
          docsSigned: 'Documents signed',
          docsTrend: 'signatures',
        },
        projects: {
          title: 'Projects & sprints',
          empty: 'No projects yet',
          methodology: 'Methodology',
          key: 'Key',
        },
        focus: {
          title: 'Focus tasks',
          columns: {
            id: 'ID',
            title: 'Title',
            status: 'Status',
            assignee: 'Assignee',
            due: 'Due date',
          },
          empty: 'No assigned tasks found',
        },
      },
      integrations: {
        title: 'Active integrations',
        count: '{{count}} connected',
        lastSync: 'Last exchange',
        test: 'Test connection',
        sync: 'Queue sync',
        logs: 'Logs',
        payloadLabel: 'Payload (JSON)',
        sandboxTitle: 'Sandboxes',
        sandboxRun: 'Run sandbox',
        queueStatus: 'Queue status',
        queued: 'Task queued for background processing',
        eager: 'Queue is running locally in eager mode.',
        resultTitle: 'Result',
        noIntegrations: 'No integrations configured yet',
        noLogs: 'Logs will appear after the first sync',
        sandboxNote: 'Use sandboxes to validate payloads without hitting external services.',
      },
      auth: {
        loginTitle: 'Sign in',
        registerTitle: 'Sign up',
        email: 'Email',
        password: 'Password',
        submit: 'Continue',
        haveAccount: 'Already have an account?',
        noAccount: "Don't have an account yet?",
        goLogin: 'Sign in',
        goRegister: 'Create account',
        registerSuccess: 'Account created! Redirecting to login…',
      },
      common: {
        loading: 'Loading…',
        retry: 'Try again',
      },
    },
  },
  ru: {
    translation: {
      brand: {
        tagline: 'Украинская платформа управления продуктом',
      },
      language: {
        label: 'Язык',
        ua: 'Українська',
        en: 'English',
        ru: 'Русский',
      },
      theme: {
        light: 'Светлая тема',
        dark: 'Тёмная тема',
        toggle: 'Переключить тему',
      },
      nav: {
        platform: 'Платформа',
        management: 'Управление',
        admin: 'Администрирование',
        dashboard: 'Дашборд',
        tasks: 'Задачи',
        docs: 'Документы',
        support: 'Поддержка',
        integrations: 'Integration Hub',
        analytics: 'Аналитика',
        settings: 'Настройки',
        marketplace: 'Маркетплейс',
        users: 'Пользователи и роли',
        audit: 'Аудит и безопасность',
      },
      topbar: {
        welcome: 'Добро пожаловать, {{name}}!',
        description:
          'Единая панель управления задачами, документами, сервисом поддержки и интеграциями.',
        logout: 'Выйти',
      },
      dashboard: {
        modulesHeading: 'Витрина модулей',
        modulesDescription:
          'Убедитесь, как UA FLOW объединяет практики Atlassian и украинские требования.',
        cards: {
          kanban: {
            title: 'Kanban-доска',
            description: 'Контроль лимитов WIP и статусов задач в реальном времени.',
            cardsLabel: 'карточек',
          },
          scrum: {
            title: 'Scrum-спринт',
            description: 'Планируйте спринты, замеряйте velocity и автоматически строьте отчёты.',
          },
          docs: {
            title: 'Документация',
            description: 'Wiki, версионирование и подписание документов КЭП.',
            signed: 'КЭП подтверждён',
            pending: 'Ожидает подпись',
            version: 'Версия {{value}}',
          },
          support: {
            title: 'Тикеты поддержки',
            description: 'SLA, маршрутизация и чат с клиентом через веб или Telegram.',
          },
        },
        stats: {
          activeTasks: 'Активных задач',
          activeTrend: 'за неделю',
          sla: 'Средний SLA (часы)',
          slaTrend: 'быстрее, чем раньше',
          docsSigned: 'Документов подписано',
          docsTrend: 'подписей',
        },
        projects: {
          title: 'Проекты и спринты',
          empty: 'У вас пока нет проектов',
          methodology: 'Методология',
          key: 'Ключ',
        },
        focus: {
          title: 'Фокусные задачи',
          columns: {
            id: 'ID',
            title: 'Название',
            status: 'Статус',
            assignee: 'Исполнитель',
            due: 'Срок',
          },
          empty: 'Назначенные задачи не найдены',
        },
      },
      integrations: {
        title: 'Активные интеграции',
        count: '{{count}} подключено',
        lastSync: 'Последний обмен',
        test: 'Проверить соединение',
        sync: 'Поставить в очередь',
        logs: 'Логи',
        payloadLabel: 'Payload (JSON)',
        sandboxTitle: 'Песочницы',
        sandboxRun: 'Запустить песочницу',
        queueStatus: 'Статус очереди',
        queued: 'Задача отправлена в очередь',
        eager: 'Очередь работает локально (режим eager).',
        resultTitle: 'Результат',
        noIntegrations: 'Интеграции не настроены',
        noLogs: 'Логи появятся после синхронизации',
        sandboxNote: 'Песочницы помогают тестировать payload без внешних API.',
      },
      auth: {
        loginTitle: 'Вход',
        registerTitle: 'Регистрация',
        email: 'Email',
        password: 'Пароль',
        submit: 'Продолжить',
        haveAccount: 'Уже есть аккаунт?',
        noAccount: 'Ещё нет аккаунта?',
        goLogin: 'Войти',
        goRegister: 'Создать аккаунт',
        registerSuccess: 'Аккаунт создан! Перенаправляем на вход…',
      },
      common: {
        loading: 'Загрузка…',
        retry: 'Повторить',
      },
    },
  },
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'ua',
    supportedLngs: ['ua', 'en', 'ru'],
    detection: {
      order: ['querystring', 'localStorage', 'navigator'],
      caches: ['localStorage'],
    },
    interpolation: {
      escapeValue: false,
    },
  })

export const languages = [
  { code: 'ua', label: resources.ua.translation.language.ua },
  { code: 'en', label: resources.en.translation.language.en },
  { code: 'ru', label: resources.ru.translation.language.ru },
]

export default i18n

