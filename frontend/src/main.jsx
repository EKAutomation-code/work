import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BookOpen,
  CalendarDays,
  Check,
  Download,
  Eye,
  EyeOff,
  GraduationCap,
  Home,
  MessageCircle,
  Moon,
  MoreHorizontal,
  Paperclip,
  Send,
  ShieldCheck,
  Star,
  Sun,
  Trash2,
  Trophy,
  User,
  X
} from "lucide-react";

import { api, getToken, logout, setToken, uploadFileWithPresign } from "./api";
import "./styles.css";

const subjects = [
  "Математика",
  "Русский язык",
  "Биология",
  "Химия",
  "Физика",
  "Информатика",
  "История",
  "Обществознание",
  "Английский язык",
  "Литература",
  "География"
];

function RatingStars({ value = 0, size = 14, count = 5 }) {
  return (
    <span className="stars" aria-label={`Рейтинг ${value} из 5`}>
      {Array.from({ length: count }, (_, index) => (
        <Star key={index} size={size} className={index < Math.round(value) ? "star filled" : "star"} />
      ))}
    </span>
  );
}

function pluralizeRussian(count, one, few, many) {
  const mod10 = count % 10;
  const mod100 = count % 100;

  if (mod100 >= 11 && mod100 <= 14) return many;
  if (mod10 === 1) return one;
  if (mod10 >= 2 && mod10 <= 4) return few;
  return many;
}

function toDateTimeLocalValue(value) {
  if (!value) return "";
  const date = new Date(value);
  const pad = (part) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function shortDateLabel(value) {
  if (!value) return "Дата пока не выбрана";
  return new Date(value).toLocaleString("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function buildUpcomingDays(value) {
  const target = value ? new Date(value) : null;
  const base = target && !Number.isNaN(target.getTime()) ? target : new Date();
  const start = new Date(base);
  start.setHours(0, 0, 0, 0);

  return Array.from({ length: 5 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    const sameDay = target
      ? day.getFullYear() === target.getFullYear() &&
        day.getMonth() === target.getMonth() &&
        day.getDate() === target.getDate()
      : false;

    return {
      key: day.toISOString(),
      label: day.toLocaleDateString("ru-RU", { weekday: "short" }),
      date: day.toLocaleDateString("ru-RU", { day: "numeric", month: "short" }),
      active: sameDay
    };
  });
}

function AvatarBadge({ user, label, className = "", style }) {
  if (user?.avatar_url) {
    return <img className={`avatar avatar-image ${className}`.trim()} style={style} src={user.avatar_url} alt={label} />;
  }
  return <div className={`avatar ${className}`.trim()} style={style}>{label?.slice(0, 1) || "?"}</div>;
}

function ImageLightbox({ image, onClose }) {
  if (!image?.src) return null;

  return (
    <div className="image-lightbox" role="dialog" aria-modal="true" onClick={onClose}>
      <button className="image-lightbox-close" type="button" aria-label="Закрыть" onClick={onClose}>
        <X size={18} />
      </button>
      <img
        className="image-lightbox-image"
        src={image.src}
        alt={image.alt}
        onClick={(event) => event.stopPropagation()}
      />
    </div>
  );
}

function isPreviewableImage(message) {
  return Boolean(message?.is_image && message?.file_url);
}

function PasswordInput({ value, onChange, placeholder }) {
  const [visible, setVisible] = useState(false);

  return (
    <label className="password-control">
      <input
        type={visible ? "text" : "password"}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
      <button
        className="password-toggle"
        type="button"
        onClick={() => setVisible((current) => !current)}
        aria-label="Показать пароль"
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </label>
  );
}

function Brand({ onClick }) {
  return (
    <button className={`brand ${onClick ? "brand-button" : ""}`} type="button" onClick={onClick}>
      <div className="mark">
        <span>Б</span>
        <b>+</b>
      </div>
      <h1>ПлюсБаллы</h1>
    </button>
  );
}

function StaticBrand() {
  return <AuthBrand />;
}

function AuthBrand() {
  return (
    <div className="brand">
      <div className="mark">
        <span>Б</span>
        <b>+</b>
      </div>
      <h1>ПлюсБаллы</h1>
    </div>
  );
}

function HomeOverview({ currentUser, onOpenPrimary }) {
  const isTutor = currentUser.role === "tutor";

  const highlights = isTutor
    ? [
        { title: "Все ученики под рукой", text: "Следите за заданиями, ответами и перепиской без лишней суеты." },
        { title: "Материалы в одном месте", text: "Публикуйте задания, прикладывайте файлы и быстро проверяйте работы." },
        { title: "Понятный рабочий ритм", text: "Чаты, комментарии и оценки помогают держать процесс собранным." }
      ]
    : [
        { title: "Подготовка без хаоса", text: "Репетиторы, задания, чат и прогресс собраны в одном кабинете." },
        { title: "Быстрый доступ к материалам", text: "Все нужные файлы и ответы всегда рядом и не теряются." },
        { title: "Понятный маршрут", text: "Сразу видно, что задано, что проверено и где нужен следующий шаг." }
      ];

  const quickActions = isTutor
    ? [
        { label: "Открыть задания", tab: "homework" },
        { label: "Перейти в чаты", tab: "chats" },
        { label: "Настроить предложение", tab: "offer" }
      ]
    : [
        { label: "Найти репетитора", tab: "catalog" },
        { label: "Открыть задания", tab: "homework" },
        { label: "Перейти в чаты", tab: "chats" }
      ];

  return (
    <section className="stack">
      <div className="card home-hero">
        <div className="home-hero-copy">
          <h3>Онлайн-школа в одном кабинете</h3>
          <p className="summary" style={{ maxWidth: "100%" }}>
            {isTutor
              ? "Ведите занятия, публикуйте задания, проверяйте ответы и общайтесь с учениками в одном кабинете."
              : "Выбирайте преподавателей, получайте задания, отправляйте ответы и следите за своим прогрессом в одном месте."}
          </p>
        </div>
        <div className="home-actions">
          {quickActions.map((action) => (
            <button key={action.tab} className="primary home-action-btn" type="button" onClick={() => onOpenPrimary(action.tab)}>
              {action.label}
            </button>
          ))}
        </div>
      </div>

      <div className="home-grid">
        {highlights.map((item) => (
          <article key={item.title} className="card home-feature">
            <h4>{item.title}</h4>
            <p>{item.text}</p>
          </article>
        ))}
      </div>

      <div className="home-bottom-grid">
        <article className="card home-panel home-panel-wide">
          <h3 style={{ marginTop: 0 }}>Как все устроено</h3>
          <div className="stack">
            <div className="home-step">
              <span className="pill">1</span>
              <p>{isTutor ? "Создайте предложение и укажите формат занятий." : "Выберите преподавателя по предмету и формату."}</p>
            </div>
            <div className="home-step">
              <span className="pill">2</span>
              <p>{isTutor ? "Публикуйте задания и прикладывайте материалы." : "Получайте задания, материалы и пояснения в личном кабинете."}</p>
            </div>
            <div className="home-step">
              <span className="pill">3</span>
              <p>{isTutor ? "Проверяйте ответы, ставьте оценки и оставляйте комментарии." : "Отправляйте ответы, смотрите оценки и держите связь в чате."}</p>
            </div>
          </div>
        </article>

        <article className="card home-panel home-panel-side">
          <h3 style={{ marginTop: 0 }}>Почему это удобно</h3>
          <div className="stack">
            <div className="meta"><strong>Один кабинет:</strong><span>все занятия, файлы и переписка под рукой.</span></div>
            <div className="meta"><strong>Прозрачный прогресс:</strong><span>видно оценки, ответы и текущий темп.</span></div>
            <div className="meta"><strong>Меньше рутины:</strong><span>ничего не теряется между чатами и файлами.</span></div>
          </div>
        </article>
      </div>
    </section>
  );
}

function UtilityMenu({ dark, onToggleTheme, onOpenAdminLogin, showAdminEntry = true }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function closeMenu(event) {
      if (!event.target.closest("[data-utility-menu]")) {
        setOpen(false);
      }
    }

    window.addEventListener("click", closeMenu);
    return () => window.removeEventListener("click", closeMenu);
  }, []);

  return (
    <div className="utility-menu" data-utility-menu>
      <button
        className="utility-menu-trigger"
        type="button"
        aria-label="Открыть меню"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <MoreHorizontal size={20} />
      </button>
      <div className="utility-menu-popover" hidden={!open}>
        <div className="utility-menu-title">Настройки</div>
        <button className="theme-toggle" type="button" onClick={onToggleTheme}>
          {dark ? <Sun size={18} /> : <Moon size={18} />}
          <span>{dark ? "Светлая тема" : "Темная тема"}</span>
        </button>
        {showAdminEntry && (
          <button
            className="theme-toggle"
            type="button"
            onClick={() => {
              setOpen(false);
              onOpenAdminLogin();
            }}
          >
            <ShieldCheck size={18} />
            <span>Вход в админку</span>
          </button>
        )}
      </div>
    </div>
  );
}

function Auth({ onLoggedIn }) {
  const [mode, setMode] = useState("login");
  const [role, setRole] = useState("student");
  const [kycConsent, setKycConsent] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event) {
    event.preventDefault();
    setMessage("");

    try {
      if (mode === "register") {
        if (role === "tutor" && !kycConsent) {
          setMessage("Для регистрации репетитора нужно согласиться на KYC-проверку.");
          return;
        }

        await api("/auth/register", {
          method: "POST",
          body: { role, full_name: fullName, email, password }
        });
        setMessage("Аккаунт создан. Код подтверждения пока выводится в логах backend-контейнера.");
        setMode("verify");
        return;
      }

      if (mode === "verify") {
        await api("/auth/verify-email", { method: "POST", body: { email, code } });
        setMessage("Email подтвержден. Теперь дождитесь одобрения аккаунта в админке.");
        setMode("login");
        return;
      }

      const token = await api("/auth/login", {
        method: "POST",
        body: { email, password, email_code: code || "000000" }
      });
      setToken(token.access_token, rememberMe);
      await onLoggedIn();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function requestCode() {
    try {
      await api("/auth/request-login-code", { method: "POST", body: { email } });
      setMessage("Код отправлен. В dev-режиме он виден в логах backend-контейнера.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="auth-screen">
      <div className="auth-visual">
        <AuthBrand />
        <h1>Подготовка и занятия в одном красивом кабинете</h1>
        <p>
          Преподаватели, задания, видеоуроки, чат и материалы собраны в одном
          пространстве. Ученику проще держать темп, а репетитору удобно вести
          каждое занятие и каждого ученика без лишней рутины.
        </p>
      </div>
      <div className="auth-panel">
        <div className="auth-switch" aria-label="Вход или регистрация">
          <button className={`small-btn auth-tab-btn ${mode === "login" ? "active" : ""}`} type="button" onClick={() => setMode("login")}>
            Вход
          </button>
          <button className={`small-btn auth-tab-btn ${mode === "register" ? "active" : ""}`} type="button" onClick={() => setMode("register")}>
            Регистрация
          </button>
        </div>
        <form className="auth-card form" onSubmit={submit}>
          <div className="eyebrow">{mode === "register" ? "Новый аккаунт" : mode === "verify" ? "Подтверждение" : "Добро пожаловать"}</div>
          <h2>{mode === "register" ? "Создание аккаунта" : mode === "verify" ? "Подтверждение email" : "Вход в кабинет"}</h2>
          {mode === "register" && (
            <>
              <select value={role} onChange={(event) => setRole(event.target.value)}>
                <option value="student">Я ученик</option>
                <option value="tutor">Я репетитор</option>
              </select>
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Имя и фамилия" />
            </>
          )}
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
          {mode !== "verify" && <PasswordInput value={password} onChange={setPassword} placeholder="Пароль" />}
          {mode === "register" && role === "tutor" && (
            <label className="consent-row">
              <input type="checkbox" checked={kycConsent} onChange={(event) => setKycConsent(event.target.checked)} />
              <span>Согласен пройти проверку личности преподавателя (KYC)</span>
            </label>
          )}
          {(mode === "verify" || mode === "login") && (
            <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="Код из письма" />
          )}
          {mode === "login" && (
            <label className="consent-row">
              <input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} />
              <span>Запомнить меня</span>
            </label>
          )}
          {mode === "login" && (
            <button className="small-btn" type="button" onClick={requestCode}>
              Получить код на почту
            </button>
          )}
          <button className="primary" type="submit">
            {mode === "register" ? "Создать личный кабинет" : mode === "verify" ? "Подтвердить email" : "Войти"}
          </button>
          {message && <div className="notice">{message}</div>}
        </form>
      </div>
    </section>
  );
}

function AdminDirectory({ users, kind, onApprove, onDelete, message }) {
  const filteredUsers = users.filter((user) => {
    if (kind === "students") return user.role === "student";
    if (kind === "teachers") return user.role === "tutor";
    return user.approval_status === "pending";
  });

  const titleMap = {
    students: "Все ученики",
    teachers: "Все учителя",
    moderation: "Модерация регистрации"
  };

  return (
    <section>
      <div className="section-title">
        <h3>{titleMap[kind]}</h3>
        <span className="pill">{filteredUsers.length}</span>
      </div>
      {message && <div className="notice" style={{ marginBottom: 12 }}>{message}</div>}
      <div className="stack">
        {filteredUsers.length === 0 ? (
          <div className="empty">В этом разделе пока никого нет.</div>
        ) : filteredUsers.map((user) => (
          <article className="card" key={user.id}>
            <div className="teacher-card">
              <div className="avatar">{user.full_name.slice(0, 1)}</div>
              <div>
                <h4>{user.full_name}</h4>
                <div className="meta">
                  <span>{user.email}</span>
                  <span>{user.role === "tutor" ? "репетитор" : "ученик"}</span>
                  <span>{user.approval_status}</span>
                  {user.role === "tutor" && <span>KYC: {user.kyc_verified ? "пройден" : "не пройден"}</span>}
                </div>
              </div>
              <div className="review-actions">
                {kind === "moderation" && (
                  <>
                    <button className="small-btn" type="button" onClick={() => onApprove(user, "approved")}>
                      <Check size={14} />
                      Одобрить
                    </button>
                    <button className="small-btn danger" type="button" onClick={() => onApprove(user, "rejected")}>
                      Отклонить
                    </button>
                  </>
                )}
                <button className="small-btn danger" type="button" onClick={() => onDelete(user)}>
                  <Trash2 size={14} />
                  Удалить
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function AdminShell({ dark, setDark, onLogout }) {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState("");
  const [tab, setTab] = useState("students");

  async function loadUsers() {
    try {
      setUsers(await api("/admin/users"));
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function approve(user, status) {
    try {
      await api(`/admin/users/${user.id}/approval`, {
        method: "PATCH",
        body: { status, kyc_verified: user.role === "tutor" ? true : user.kyc_verified }
      });
      await loadUsers();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function removeUser(user) {
    const confirmed = window.confirm(`Удалить аккаунт ${user.full_name}? Это действие нельзя отменить.`);
    if (!confirmed) return;

    try {
      const result = await api(`/admin/users/${user.id}`, {
        method: "DELETE"
      });
      setMessage(result.status === "deleted" ? "Аккаунт удален." : "Аккаунт удален.");
      await loadUsers();
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  const pageMeta = {
    students: {
      eyebrow: "Админ-панель",
      title: "Ученики",
      summary: "Все зарегистрированные ученики в одном списке."
    },
    teachers: {
      eyebrow: "Админ-панель",
      title: "Учителя",
      summary: "Список репетиторов со статусом проверки и доступа."
    },
    moderation: {
      eyebrow: "Админ-панель",
      title: "Модерация",
      summary: "Проверяйте новые заявки и подтверждайте аккаунты."
    }
  };

  const meta = pageMeta[tab];

  return (
    <div className="shell">
      <aside className="sidebar">
        <StaticBrand />
        <nav className="nav" aria-label="Разделы админки">
          <button className={tab === "students" ? "active" : ""} type="button" onClick={() => setTab("students")}>
            <GraduationCap size={20} />
            <span>Ученики</span>
          </button>
          <button className={tab === "teachers" ? "active" : ""} type="button" onClick={() => setTab("teachers")}>
            <BookOpen size={20} />
            <span>Учителя</span>
          </button>
          <button className={tab === "moderation" ? "active" : ""} type="button" onClick={() => setTab("moderation")}>
            <ShieldCheck size={20} />
            <span>Модерация</span>
          </button>
        </nav>
        <div className="new-user">
          <button className="ghost" type="button" onClick={loadUsers}>Обновить списки</button>
          <button className="ghost" type="button" onClick={onLogout}>Выйти из админки</button>
        </div>
      </aside>
      <main className={tab === "chats" ? "page-chat" : ""}>
        <header className={tab === "chats" ? "topbar topbar-compact" : "topbar"}>
          <div>
            <div className="eyebrow">{meta.eyebrow}</div>
            {tab === "home" ? (
              <div className="topbar-branding">
                <div className="mark topbar-mark" aria-hidden="true">
                  <span>Б</span>
                  <b>+</b>
                </div>
                <h2>{meta.title}</h2>
              </div>
            ) : (
              <h2>{meta.title}</h2>
            )}
            <p className="summary">{meta.summary}</p>
          </div>
        </header>
        <AdminDirectory users={users} kind={tab} onApprove={approve} onDelete={removeUser} message={message} />
      </main>
      <UtilityMenu
        dark={dark}
        onToggleTheme={() => setDark((value) => !value)}
        onOpenAdminLogin={() => {}}
        showAdminEntry={false}
      />
    </div>
  );
}

function AdminLogin({ onBack, onSuccess }) {
  const [login, setLogin] = useState("egorburakov");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event) {
    event.preventDefault();
    setMessage("");

    try {
      const token = await api(
        `/auth/admin-login?login=${encodeURIComponent(login)}&password=${encodeURIComponent(password)}`,
        { method: "POST" }
      );
      setToken(token.access_token);
      onSuccess();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="auth-screen">
      <div className="auth-visual">
        <AuthBrand />
        <h1>Админ-панель платформы</h1>
        <p>
          Отсюда можно подтверждать аккаунты, просматривать списки учеников и
          учителей и модерировать регистрацию новых пользователей.
        </p>
      </div>
      <div className="auth-panel">
        <form className="auth-card form" onSubmit={submit}>
          <h2>Вход в админку</h2>
          <input value={login} onChange={(event) => setLogin(event.target.value)} placeholder="Логин" />
          <PasswordInput value={password} onChange={setPassword} placeholder="Пароль" />
          <div className="actions">
            <button className="small-btn" type="button" onClick={onBack}>Назад</button>
            <button className="primary" type="submit">Войти</button>
          </div>
          {message && <div className="notice">{message}</div>}
        </form>
      </div>
    </section>
  );
}

function TutorOffer() {
  const [subject, setSubject] = useState(subjects[0]);
  const [price, setPrice] = useState(1500);
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");
  const [offerReady, setOfferReady] = useState(false);
  const [packages, setPackages] = useState([]);
  const [packageForm, setPackageForm] = useState({
    title: "",
    subject: subjects[0],
    price_rub: 2500,
    description: ""
  });

  useEffect(() => {
    api("/tutors/me/offer")
      .then((offer) => {
        if (offer.subject) setSubject(offer.subject);
        if (offer.price_rub) setPrice(offer.price_rub);
        if (offer.description) setDescription(offer.description);
        setPackages(offer.packages || []);
        setOfferReady(Boolean(offer.offer_published || offer.subject || offer.price_rub || offer.description));
      })
      .catch(() => {});
  }, []);

  async function save(event) {
    event.preventDefault();
    setMessage("");

    try {
      const result = await api("/tutors/me/offer", {
        method: "PUT",
        body: { subject, price_rub: Number(price), description, offer_published: true }
      });
      setOfferReady(true);
      setMessage(result.message || "Предложение успешно создано и уже видно ученикам.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function addPackage(event) {
    event.preventDefault();
    setMessage("");

    try {
      const created = await api("/tutors/me/offers", {
        method: "POST",
        body: {
          title: packageForm.title,
          subject: packageForm.subject,
          price_rub: Number(packageForm.price_rub),
          description: packageForm.description
        }
      });
      setPackages((current) => [created, ...current]);
      setPackageForm({
        title: "",
        subject: subjects[0],
        price_rub: 2500,
        description: ""
      });
      setMessage("Дополнительное предложение сохранено.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function removePackage(id) {
    try {
      await api(`/tutors/me/offers/${id}`, {
        method: "DELETE"
      });
      setPackages((current) => current.filter((item) => item.id !== id));
      setMessage("Предложение удалено.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="offer-layout">
      <div className="stack">
        <form className="card form offer-form-card" onSubmit={save}>
          <div className="section-title">
            <h3>Основное предложение</h3>
            <span className="pill">{offerReady ? "Опубликовано" : "Черновик"}</span>
          </div>
          <div className="offer-form-grid">
            <div className="stack">
              <label className="field-label">Предмет</label>
              <select value={subject} onChange={(event) => setSubject(event.target.value)}>
                {subjects.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
            <div className="stack">
              <label className="field-label">Цена в месяц</label>
              <input type="number" min="100" step="100" value={price} onChange={(event) => setPrice(event.target.value)} />
            </div>
          </div>
          <label className="field-label">Описание</label>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Коротко расскажите, как проходят занятия, какой у вас темп и для кого подойдет этот формат." />
          <div className="offer-actions">
            <button className="primary" type="submit">Сохранить предложение</button>
            <span className="field-label">Это предложение отображается в каталоге как основное.</span>
          </div>
        </form>

        <form className="card form offer-form-card" onSubmit={addPackage}>
          <div className="section-title">
            <h3>Дополнительные предложения</h3>
            <span className="pill">{packages.length}</span>
          </div>
          <div className="offer-form-grid offer-form-grid-wide">
            <div className="stack">
              <label className="field-label">Название</label>
              <input
                value={packageForm.title}
                onChange={(event) => setPackageForm((current) => ({ ...current, title: event.target.value }))}
                placeholder="Например: Интенсив перед ЕГЭ"
              />
            </div>
            <div className="stack">
              <label className="field-label">Предмет</label>
              <select value={packageForm.subject} onChange={(event) => setPackageForm((current) => ({ ...current, subject: event.target.value }))}>
                {subjects.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
            <div className="stack">
              <label className="field-label">Цена</label>
              <input
                type="number"
                min="100"
                step="100"
                value={packageForm.price_rub}
                onChange={(event) => setPackageForm((current) => ({ ...current, price_rub: event.target.value }))}
              />
            </div>
          </div>
          <label className="field-label">Описание формата</label>
          <textarea
            value={packageForm.description}
            onChange={(event) => setPackageForm((current) => ({ ...current, description: event.target.value }))}
            placeholder="Коротко опишите, чем этот формат отличается: интенсив, разбор пробников, мини-группа и так далее."
          />
          <div className="offer-actions">
            <button className="primary" type="submit">Добавить формат</button>
            <span className="field-label">Можно сделать несколько вариантов под разный темп и бюджет.</span>
          </div>
          {message && <div className="notice">{message}</div>}
        </form>
      </div>
      <aside className="card offer-preview-card">
        <div className="section-title">
          <h3>Как это видит ученик</h3>
          <span className={`pill ${offerReady ? "" : "warn"}`}>{offerReady ? "В каталоге" : "После сохранения"}</span>
        </div>
        <article className="offer-preview">
          <div className="avatar offer-avatar">Р</div>
          <div className="stack">
            <div>
              <h4>{subject}</h4>
              <div className="meta">
                <span>{price} ₽ / месяц</span>
                <span>Онлайн-формат</span>
              </div>
            </div>
            <p>{description || "После заполнения здесь появится аккуратное описание вашего предложения для ученика."}</p>
          </div>
        </article>
        <div className="offer-published-box">
          <strong>Опубликованное предложение</strong>
          <div className="offer-published-meta">
            <span>{subject}</span>
            <span>{price} ₽ / месяц</span>
          </div>
          <p>{description || "Добавьте короткое описание, чтобы ученикам было проще понять ваш формат занятий."}</p>
        </div>
        <div className="stack">
          {packages.length === 0 ? (
            <div className="empty">Дополнительные форматы пока не добавлены.</div>
          ) : packages.map((item) => (
            <article className="offer-package-card" key={item.id}>
              <div className="offer-package-head">
                <strong>{item.title}</strong>
                <span className="pill">{item.price_rub} ₽</span>
              </div>
              <div className="meta">
                <span>{item.subject}</span>
              </div>
              <p>{item.description}</p>
              <button className="small-btn danger" type="button" onClick={() => removePackage(item.id)}>Удалить</button>
            </article>
          ))}
        </div>
      </aside>
    </section>
  );
}

function TutorStudentsArea() {
  const [students, setStudents] = useState([]);
  const [message, setMessage] = useState("");
  const [drafts, setDrafts] = useState({});

  async function loadStudents() {
    try {
      const data = await api("/tutors/me/students");
      setStudents(data);
      setDrafts((current) => {
        const next = { ...current };
        for (const item of data) {
          if (next[item.student_id] === undefined) {
            next[item.student_id] = toDateTimeLocalValue(item.next_lesson_at);
          }
        }
        return next;
      });
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadStudents();
  }, []);

  async function saveLesson(studentId) {
    try {
      const result = await api(`/tutors/me/students/${studentId}`, {
        method: "PATCH",
        body: {
          next_lesson_at: drafts[studentId] || null
        }
      });
      setMessage(result.message || "Следующее занятие обновлено.");
      await loadStudents();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="stack">
      <div className="section-title">
        <h3>Мои ученики</h3>
        <span className="pill">{students.length} {pluralizeRussian(students.length, "ученик", "ученика", "учеников")}</span>
      </div>
      {students.length === 0 ? (
        <div className="card empty">Пока к вам никто не прикрепился. Как только ученик выберет вас, он появится здесь.</div>
      ) : (
        <div className="students-grid">
          {students.map((student) => (
            <article key={student.student_id} className="card student-card">
              <div className="student-card-head">
                <div className="review-author">
                  <AvatarBadge user={student} label={student.full_name} />
                  <div>
                    <h4>{student.full_name}</h4>
                    <div className="meta student-meta">
                      <span>{student.email}</span>
                      <span className="student-meta-secondary">с вами с {new Date(student.enrolled_at).toLocaleDateString("ru-RU")}</span>
                    </div>
                  </div>
                </div>
                <span className="pill">Ученик</span>
              </div>

              <div className="student-schedule">
                <div className="student-schedule-copy">
                  <strong>Следующее занятие</strong>
                  <span>{shortDateLabel(student.next_lesson_at)}</span>
                </div>
                <div className="student-calendar-strip">
                  {buildUpcomingDays(student.next_lesson_at).map((day) => (
                    <div key={day.key} className={`student-day-chip ${day.active ? "active" : ""}`}>
                      <strong>{day.label}</strong>
                      <span>{day.date}</span>
                    </div>
                  ))}
                </div>
                <input
                  className="student-datetime"
                  type="datetime-local"
                  value={drafts[student.student_id] || ""}
                  onChange={(event) => setDrafts((current) => ({ ...current, [student.student_id]: event.target.value }))}
                />
              </div>

              <div className="actions">
                <button className="primary" type="button" onClick={() => saveLesson(student.student_id)}>Сохранить дату</button>
              </div>
            </article>
          ))}
        </div>
      )}
      {message && <div className="notice">{message}</div>}
    </section>
  );
}

function TutorProfilePage({ tutorId, currentUser, onBack, onEnroll }) {
  const [profile, setProfile] = useState(null);
  const [stars, setStars] = useState(5);
  const [reviewText, setReviewText] = useState("");
  const [message, setMessage] = useState("");

  async function loadProfile() {
    try {
      setProfile(await api(`/tutors/${tutorId}`));
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadProfile();
  }, [tutorId]);

  async function submitReview(event) {
    event.preventDefault();
    try {
      const result = await api(`/tutors/${tutorId}/reviews`, {
        method: "POST",
        body: { stars, text: reviewText }
      });
      setMessage(result.message || "Отзыв сохранен");
      setReviewText("");
      await loadProfile();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleEnroll() {
    const result = await onEnroll(profile.id, profile.is_enrolled);
    if (!result) return;

    setProfile((current) => (
      current
        ? {
            ...current,
            is_enrolled: !["unenrolled", "not_enrolled"].includes(result.status),
            can_review: !["unenrolled", "not_enrolled"].includes(result.status),
          }
        : current
    ));

    if (result.status === "already_enrolled") {
      setMessage("Вы уже прикреплены к этому преподавателю.");
      return;
    }

    if (result.status === "unenrolled") {
      setMessage("Вы открепились от преподавателя.");
      return;
    }

    if (result.status === "not_enrolled") {
      setMessage("Вы уже не прикреплены к этому преподавателю.");
      return;
    }

    setMessage("Ученик прикреплен к учителю. Чат уже доступен во вкладке сообщений.");
  }

  if (!profile) {
    return <div className="empty">Загружаем профиль репетитора.</div>;
  }

  return (
    <section className="stack">
      <button className="small-btn" type="button" onClick={onBack}>Назад к списку учителей</button>
      <div className="profile-hero card">
        <AvatarBadge user={profile} label={profile.full_name} className="profile-avatar" />
        <div className="profile-main">
          <h3>{profile.full_name}</h3>
          <div className="meta">
            {profile.subject && <span>{profile.subject}</span>}
            {profile.price_rub && <span>{profile.price_rub} ₽ / месяц</span>}
          </div>
          <div className="rating-panel">
            <RatingStars value={profile.average_rating} size={22} />
            <span className="rating-count rating-count-lg">{profile.review_count} отзывов</span>
          </div>
          <p>{profile.description}</p>
          {profile.bio && <p>{profile.bio}</p>}
          {(profile.education || profile.experience || profile.lesson_format) && (
            <div className="stack" style={{ marginTop: 12 }}>
              {profile.education && <div className="meta"><strong>Образование:</strong><span>{profile.education}</span></div>}
              {profile.experience && <div className="meta"><strong>Опыт:</strong><span>{profile.experience}</span></div>}
              {profile.lesson_format && <div className="meta"><strong>Формат занятий:</strong><span>{profile.lesson_format}</span></div>}
            </div>
          )}
          {profile.packages?.length > 0 && (
            <div className="offer-package-list">
              {profile.packages.map((item) => (
                <article key={item.id} className="offer-package-card">
                  <div className="offer-package-head">
                    <strong>{item.title}</strong>
                    <span className="pill">{item.price_rub} ₽</span>
                  </div>
                  <div className="meta">
                    <span>{item.subject}</span>
                  </div>
                  <p>{item.description}</p>
                </article>
              ))}
            </div>
          )}
        </div>
        {currentUser.role === "student" && (
          <button
            className={profile.is_enrolled ? "small-btn" : "primary"}
            type="button"
            onClick={handleEnroll}
          >
            {profile.is_enrolled ? "Открепиться" : "Прикрепиться"}
          </button>
        )}
      </div>

      {profile.can_review && currentUser.role === "student" && (
        <form className="card form" onSubmit={submitReview}>
          <h3 style={{ margin: 0 }}>Оставить отзыв</h3>
          <label className="field-label">Оценка</label>
          <select value={stars} onChange={(event) => setStars(Number(event.target.value))}>
            {[5, 4, 3, 2, 1].map((value) => <option value={value} key={value}>{value} звезд</option>)}
          </select>
          <label className="field-label">Текст отзыва</label>
          <textarea value={reviewText} onChange={(event) => setReviewText(event.target.value)} placeholder="Напишите, что понравилось на занятиях, как преподаватель объясняет темы и какие уже есть результаты." />
          <button className="primary" type="submit">Сохранить отзыв</button>
          {message && <div className="notice">{message}</div>}
        </form>
      )}

      <section>
        <div className="section-title">
          <h3>Отзывы</h3>
          <span className="pill">{profile.review_count}</span>
        </div>
        <div className="stack">
          {profile.reviews.length === 0 ? (
            <div className="empty">У этого репетитора пока нет отзывов.</div>
          ) : profile.reviews.map((review) => (
            <article className="card review-card" key={review.id}>
              <div className="review-head">
                <div className="review-author">
                  <AvatarBadge user={{ avatar_url: review.student_avatar_url }} label={review.student_name} />
                  <div>
                    <strong>{review.student_name}</strong>
                    <div className="meta">
                      <RatingStars value={review.stars} />
                      <span>{new Date(review.created_at).toLocaleDateString("ru-RU")}</span>
                    </div>
                  </div>
                </div>
              </div>
              <p>{review.text}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
function PersonalAccount({ currentUser, onProfileUpdated }) {
  const [message, setMessage] = useState("");
  const [profile, setProfile] = useState(null);
  const [editingBasic, setEditingBasic] = useState(false);
  const [basicForm, setBasicForm] = useState({
    full_name: currentUser.full_name || "",
    about: currentUser.about || ""
  });
  const [form, setForm] = useState({
    bio: "",
    education: "",
    experience: "",
    lesson_format: ""
  });

  useEffect(() => {
    setBasicForm({
      full_name: currentUser.full_name || "",
      about: currentUser.about || ""
    });
  }, [currentUser]);

  useEffect(() => {
    if (currentUser.role === "tutor") {
      api(`/tutors/${currentUser.id}`)
        .then((data) => {
          setProfile(data);
          setForm({
            bio: data.bio || "",
            education: data.education || "",
            experience: data.experience || "",
            lesson_format: data.lesson_format || ""
          });
        })
        .catch(() => setProfile(null));
    }
  }, [currentUser]);

  async function uploadAvatar(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const fileKey = await uploadFileWithPresign(file, "avatars");
      const updated = await api("/auth/me", {
        method: "PATCH",
        body: { avatar_file_key: fileKey }
      });
      onProfileUpdated(updated);
      setMessage("Аватарка обновлена");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function saveTutorProfile(event) {
    event.preventDefault();
    try {
      const result = await api("/tutors/me/profile", {
        method: "PATCH",
        body: form
      });
      setMessage(result.message || "Личный кабинет обновлен");
      const updated = await api(`/tutors/${currentUser.id}`);
      setProfile(updated);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function saveBasicProfile(event) {
    event.preventDefault();
    try {
      const updated = await api("/auth/me", {
        method: "PATCH",
        body: basicForm
      });
      onProfileUpdated(updated);
      setEditingBasic(false);
      setMessage("Профиль обновлен");
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="stack">
      <div className="card account-hero">
        <AvatarBadge
          user={currentUser}
          label={currentUser.full_name}
          className="profile-avatar profile-avatar-xl"
          style={{ width: 220, height: 220, minWidth: 220, minHeight: 220, fontSize: 72, borderRadius: 22 }}
        />
        <div className="profile-main">
          <div className="eyebrow">Личный кабинет</div>
          <h3>{currentUser.full_name}</h3>
          <div className="meta">
            <span>{currentUser.email}</span>
            <span>{currentUser.role === "tutor" ? "репетитор" : "ученик"}</span>
            {currentUser.role === "tutor" && profile && <span>{profile.review_count} отзывов</span>}
          </div>
          <p className="account-intro">
            {currentUser.role === "tutor"
              ? "Покажите свой стиль преподавания, сильные стороны и формат работы в одном аккуратном профиле."
              : "Поддерживайте профиль в порядке: с аватаром и понятными данными личный кабинет выглядит живее и приятнее."}
          </p>
          <div className="profile-actions">
            <label className="small-btn profile-upload">
              Загрузить аватар
              <input type="file" hidden accept="image/*" onChange={uploadAvatar} />
            </label>
            <button className="small-btn" type="button" onClick={() => setEditingBasic((value) => !value)}>
              {editingBasic ? "Скрыть редактирование" : "Изменить профиль"}
            </button>
          </div>
          {message && <div className="notice">{message}</div>}
        </div>
      </div>
      <section className={`layout ${currentUser.role === "tutor" ? "" : "layout-single"}`.trim()}>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Основная информация</h3>
          {editingBasic && (
            <div className="edit-profile-panel">
              <form className="form" onSubmit={saveBasicProfile}>
                <label className="field-label">Имя и фамилия</label>
                <input
                  value={basicForm.full_name}
                  onChange={(event) => setBasicForm((prev) => ({ ...prev, full_name: event.target.value }))}
                  placeholder="Как вас будут видеть на платформе"
                />
                <label className="field-label">Описание профиля</label>
                <textarea
                  value={basicForm.about}
                  onChange={(event) => setBasicForm((prev) => ({ ...prev, about: event.target.value }))}
                  placeholder={currentUser.role === "tutor" ? "Коротко опишите свой подход, формат работы или важные детали о себе." : "Напишите пару слов о себе, целях в учебе или том, как вам удобно заниматься."}
                />
                <button className="primary" type="submit">Сохранить изменения</button>
              </form>
            </div>
          )}
          {currentUser.role === "tutor" ? (
            profile ? (
              <>
              <div className="profile-stat-grid" style={{ marginBottom: 18 }}>
                <div className="rating-panel rating-panel-wide">
                  <span className="rating-count">{profile.review_count} отзывов</span>
                  <RatingStars value={profile.average_rating} size={26} />
                </div>
                <div className="account-mini-card">
                  <strong>Профиль преподавателя</strong>
                  <span>{form.bio || form.education || form.experience || form.lesson_format ? "Карточка уже выглядит наполненной и готовой к просмотру." : "Заполните блоки ниже, чтобы ученики сразу видели вашу подачу и опыт."}</span>
                </div>
              </div>
                <form className="form" onSubmit={saveTutorProfile}>
                  <label className="field-label">О себе</label>
                  <textarea value={form.bio} onChange={(event) => setForm((prev) => ({ ...prev, bio: event.target.value }))} placeholder="Расскажите, как вы ведете занятия, чем отличаетесь и кому особенно подходите." />
                  <label className="field-label">Образование</label>
                  <textarea value={form.education} onChange={(event) => setForm((prev) => ({ ...prev, education: event.target.value }))} placeholder="Например: МГУ, физический факультет. Курсы, сертификаты, дополнительная подготовка." />
                  <label className="field-label">Опыт</label>
                  <textarea value={form.experience} onChange={(event) => setForm((prev) => ({ ...prev, experience: event.target.value }))} placeholder="Сколько лет преподаете, с кем работали, какие результаты у учеников." />
                  <label className="field-label">Формат занятий</label>
                  <textarea value={form.lesson_format} onChange={(event) => setForm((prev) => ({ ...prev, lesson_format: event.target.value }))} placeholder="Онлайн или офлайн, частота занятий, домашние задания, разборы, чат, пробники." />
                  <button className="primary" type="submit">Сохранить личный кабинет</button>
                </form>
              </>
            ) : (
              <div className="empty">После публикации предложения здесь можно будет подробно оформить профиль преподавателя.</div>
            )
          ) : (
            <div className="profile-student-grid">
              <div className="account-mini-card">
                <strong>Личный профиль</strong>
                <span>{currentUser.about || "Аватар, имя и описание будут видны в чате, в рейтинге и в рабочем кабинете."}</span>
              </div>
              <div className="account-mini-card">
                <strong>Учебный ритм</strong>
                <span>Отсюда удобно начинать день: дальше рядом уже ждут задания, преподаватели и переписка.</span>
              </div>
            </div>
          )}
        </div>
        {currentUser.role === "tutor" && (
          <aside className="card account-preview-card">
            <h3 style={{ marginTop: 0 }}>Карточка для ученика</h3>
            <div className="stack">
              <div className="account-mini-card">
                <strong>О себе</strong>
                <span>{profile?.bio || "После заполнения здесь появится ваше описание."}</span>
              </div>
              <div className="account-mini-card">
                <strong>Образование</strong>
                <span>{profile?.education || "Пока не заполнено"}</span>
              </div>
              <div className="account-mini-card">
                <strong>Опыт</strong>
                <span>{profile?.experience || "Пока не заполнено"}</span>
              </div>
              <div className="account-mini-card">
                <strong>Формат занятий</strong>
                <span>{profile?.lesson_format || "Пока не заполнено"}</span>
              </div>
            </div>
          </aside>
        )}
      </section>
    </section>
  );
}

function TutorsCatalog({ onOpenProfile }) {
  const [tutors, setTutors] = useState([]);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api(`/tutors${subject ? `?subject=${encodeURIComponent(subject)}` : ""}`)
      .then(setTutors)
      .catch(() => setTutors([]));
  }, [subject]);

  async function toggleEnrollment(tutorId, isEnrolled) {
    try {
      const result = await api(`/tutors/${tutorId}/enroll`, {
        method: isEnrolled ? "DELETE" : "POST"
      });
      setTutors((current) =>
        current.map((tutor) =>
          tutor.id === tutorId ? { ...tutor, is_enrolled: !isEnrolled } : tutor
        )
      );
      setMessage(
        result.status === "already_enrolled"
          ? "Вы уже прикреплены к этому преподавателю."
          : result.status === "unenrolled"
            ? "Вы открепились от преподавателя."
            : result.status === "not_enrolled"
              ? "Вы уже не прикреплены к этому преподавателю."
              : "Ученик прикреплен к учителю. Чат уже доступен во вкладке сообщений."
      );
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section>
      <div className="section-title">
        <h3>Предложения учителей</h3>
      </div>
      <div className="card form" style={{ marginBottom: 16 }}>
        <select value={subject} onChange={(event) => setSubject(event.target.value)}>
          <option value="">Все предметы</option>
          {subjects.map((item) => <option key={item}>{item}</option>)}
        </select>
        {message && <div className="notice">{message}</div>}
      </div>
      <div className="stack">
        {tutors.length === 0 ? (
          <div className="empty">Пока нет опубликованных предложений по выбранному фильтру.</div>
        ) : tutors.map((tutor) => (
          <article className="card teacher-card" key={tutor.id}>
            <AvatarBadge user={tutor} label={tutor.full_name} />
            <div>
              <h4>{tutor.full_name}</h4>
              <div className="meta">
                <RatingStars value={tutor.average_rating} />
                <span>{tutor.review_count} отзывов</span>
                {tutor.offer_count > 1 && <span>{tutor.offer_count} формата занятий</span>}
              </div>
              <div className="teacher-card-keyline">
                <span className="teacher-card-subject">{tutor.subject}</span>
                <span className="teacher-card-price">{tutor.price_rub} ₽ / месяц</span>
              </div>
              <p>{tutor.description}</p>
            </div>
            <div className="review-actions">
              <button className="small-btn" type="button" onClick={() => onOpenProfile(tutor.id)}>Профиль</button>
              <button
                className="small-btn"
                type="button"
                onClick={() => toggleEnrollment(tutor.id, tutor.is_enrolled)}
              >
                {tutor.is_enrolled ? "Открепиться" : "Прикрепиться"}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function StudentHomeworkArea() {
  const [homework, setHomework] = useState([]);
  const [activeHomeworkId, setActiveHomeworkId] = useState(null);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [lightboxImage, setLightboxImage] = useState(null);

  async function loadHomework() {
    try {
      const data = await api("/homework");
      setHomework(data);
      setActiveHomeworkId((current) => current || data[0]?.id || null);
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadHomework();
  }, []);

  async function submitHomework(event) {
    event.preventDefault();
    if (!file || !activeHomeworkId) {
      setMessage("Выберите задание и файл ответа.");
      return;
    }

    try {
      const fileKey = await uploadFileWithPresign(file);
      const submission = await api("/homework/submissions", {
        method: "POST",
        body: { homework_id: Number(activeHomeworkId), file_key: fileKey, file_name: file.name }
      });
      setHomework((current) =>
        current.map((item) =>
          item.id === Number(activeHomeworkId) ? { ...item, submission } : item
        )
      );
      setMessage("Ответ отправлен.");
      setFile(null);
    } catch (error) {
      setMessage(error.message);
    }
  }

  const activeHomework = homework.find((item) => item.id === activeHomeworkId);

  return (
    <section className="homework-workspace">
      <aside className="card homework-list-panel">
        <div className="section-title">
          <h3>Домашние задания</h3>
          <span className="pill hot">{homework.length}</span>
        </div>
        <button className="small-btn" type="button" onClick={loadHomework}>Обновить</button>
        <div className="stack">
          {homework.length === 0 ? (
            <div className="empty">Задания появятся только от тех репетиторов, к которым вы прикреплены.</div>
          ) : homework.map((item) => (
            <button
              key={item.id}
              className={`homework-item ${activeHomeworkId === item.id ? "active" : ""}`}
              type="button"
              onClick={() => setActiveHomeworkId(item.id)}
            >
              <div>
                <strong>{item.title}</strong>
                <div className="meta">
                  <span>{item.tutor_name}</span>
                  <span>{item.target_student_id ? "Личное задание" : "Общее задание"}</span>
                  <span>{new Date(item.created_at).toLocaleDateString("ru-RU")}</span>
                </div>
              </div>
              <span className={`pill ${item.submission?.grade ? "" : item.submission ? "warn" : "hot"}`}>
                {item.submission?.grade ? `${item.submission.grade}/5` : item.submission ? "Ожидает" : "Без ответа"}
              </span>
            </button>
          ))}
        </div>
      </aside>

      <div className="stack">
        {activeHomework ? (
          <>
            <article className="card homework-detail">
              <div className="homework-head">
                <div>
                  <h3 style={{ margin: "0 0 8px" }}>{activeHomework.title}</h3>
                  <div className="meta">
                    <span>{activeHomework.tutor_name}</span>
                    <span>{activeHomework.target_student_id ? "Назначено лично вам" : "Доступно всем ученикам преподавателя"}</span>
                    <span>{new Date(activeHomework.created_at).toLocaleDateString("ru-RU")}</span>
                  </div>
                </div>
                <span className="pill">{activeHomework.attachment_file_name ? "Есть вложение" : "Текстовое задание"}</span>
              </div>
              <p>{activeHomework.description}</p>
              {activeHomework.attachment_file_url && activeHomework.is_image && (
                <button
                  className="homework-image-button"
                  type="button"
                  onClick={() => setLightboxImage({ src: activeHomework.attachment_file_url, alt: activeHomework.attachment_file_name || activeHomework.title })}
                >
                  <img className="homework-preview-image" src={activeHomework.attachment_file_url} alt={activeHomework.attachment_file_name || activeHomework.title} />
                </button>
              )}
              {activeHomework.attachment_file_url && !activeHomework.is_image && (
                <a className="chat-file-link" href={activeHomework.attachment_file_url} target="_blank" rel="noreferrer" download={activeHomework.attachment_file_name}>
                  <div className="attach-note">
                    <Paperclip size={14} />
                    <span>{activeHomework.attachment_file_name}</span>
                  </div>
                  <span className="chat-file-action">
                    <Download size={14} />
                    Скачать задание
                  </span>
                </a>
              )}
            </article>

            <article className="card homework-detail">
              <div className="section-title">
                <h3>Ответ и проверка</h3>
                <span className={`pill ${activeHomework.submission?.grade ? "" : activeHomework.submission ? "warn" : "hot"}`}>
                  {activeHomework.submission?.grade ? `Оценка ${activeHomework.submission.grade}/5` : activeHomework.submission ? "Ожидает оценивания" : "Ответ не отправлен"}
                </span>
              </div>

              {activeHomework.submission && (
                <div className="stack">
                  {activeHomework.submission.is_image ? (
                    <button
                      className="homework-image-button"
                      type="button"
                      onClick={() => setLightboxImage({ src: activeHomework.submission.file_url, alt: activeHomework.submission.file_name })}
                    >
                      <img className="homework-preview-image" src={activeHomework.submission.file_url} alt={activeHomework.submission.file_name} />
                    </button>
                  ) : (
                    <a className="chat-file-link" href={activeHomework.submission.file_url} target="_blank" rel="noreferrer" download={activeHomework.submission.file_name}>
                      <div className="attach-note">
                        <Paperclip size={14} />
                        <span>{activeHomework.submission.file_name}</span>
                      </div>
                      <span className="chat-file-action">
                        <Download size={14} />
                        Скачать ответ
                      </span>
                    </a>
                  )}
                  <div className="meta">
                    <span>{new Date(activeHomework.submission.created_at).toLocaleString("ru-RU")}</span>
                  </div>
                </div>
              )}

              <div className="card" style={{ padding: 14 }}>
                <strong>Комментарий преподавателя</strong>
                <p style={{ margin: "8px 0 0" }}>{activeHomework.submission?.teacher_comment || "Комментарий появится после проверки."}</p>
              </div>

              <form className="form" onSubmit={submitHomework}>
                <label className="file-picker">
                  <input className="file-picker-input" type="file" accept="image/*,.pdf" onChange={(event) => setFile(event.target.files?.[0] || null)} />
                  <span className="small-btn">
                    <Paperclip size={14} />
                    Выбрать файл
                  </span>
                  <span className="file-picker-name">{file?.name || "Файл не выбран"}</span>
                </label>
                {file && (
                  <div className="attach-note">
                    <Paperclip size={14} />
                    <span>{file.name}</span>
                  </div>
                )}
                <button className="primary" type="submit">Прикрепить ответ</button>
                {message && <div className="notice">{message}</div>}
              </form>
            </article>
          </>
        ) : (
          <div className="empty">Выберите задание слева, чтобы посмотреть его полностью.</div>
        )}
      </div>
      <ImageLightbox image={lightboxImage} onClose={() => setLightboxImage(null)} />
    </section>
  );
}

function TutorHomeworkArea() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [attachmentFile, setAttachmentFile] = useState(null);
  const [homework, setHomework] = useState([]);
  const [students, setStudents] = useState([]);
  const [targetStudentId, setTargetStudentId] = useState("");
  const [activeHomeworkId, setActiveHomeworkId] = useState(null);
  const [message, setMessage] = useState("");
  const [reviewDrafts, setReviewDrafts] = useState({});
  const [lightboxImage, setLightboxImage] = useState(null);

  async function loadHomework() {
    try {
      const data = await api("/homework/my");
      setHomework(data);
      setActiveHomeworkId((current) => current || data[0]?.id || null);
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadHomework();
    api("/tutors/me/students").then(setStudents).catch(() => setStudents([]));
  }, []);

  async function createHomework(event) {
    event.preventDefault();
    setMessage("");

    try {
      let fileKey = null;
      if (attachmentFile) {
        fileKey = await uploadFileWithPresign(attachmentFile);
      }
      await api("/homework", {
        method: "POST",
        body: {
          title,
          description,
          target_student_id: targetStudentId ? Number(targetStudentId) : null,
          attachment_file_key: fileKey,
          attachment_file_name: attachmentFile?.name || null
        }
      });
      setTitle("");
      setDescription("");
      setTargetStudentId("");
      setAttachmentFile(null);
      setMessage("Задание опубликовано.");
      await loadHomework();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function saveReview(submission) {
    const draft = reviewDrafts[submission.id] || {
      grade: submission.grade || 5,
      teacher_comment: submission.teacher_comment || ""
    };

    try {
      await api(`/homework/submissions/${submission.id}/grade`, {
        method: "PATCH",
        body: {
          grade: Number(draft.grade),
          teacher_comment: draft.teacher_comment
        }
      });
      setMessage("Оценка и комментарий сохранены.");
      await loadHomework();
    } catch (error) {
      setMessage(error.message);
    }
  }

  const activeHomework = homework.find((item) => item.id === activeHomeworkId);

  return (
    <section className="homework-workspace">
      <aside className="card homework-list-panel">
        <div className="section-title">
          <h3>Мои задания</h3>
          <span className="pill">Для прикрепленных учеников</span>
        </div>
        <button className="small-btn" type="button" onClick={loadHomework}>Обновить</button>
        <div className="stack">
          {homework.length === 0 ? (
            <div className="empty">Пока нет опубликованных заданий.</div>
          ) : homework.map((item) => (
            <button
              key={item.id}
              className={`homework-item ${activeHomeworkId === item.id ? "active" : ""}`}
              type="button"
              onClick={() => setActiveHomeworkId(item.id)}
            >
              <div>
                <strong>{item.title}</strong>
                <div className="meta">
                  <span>{new Date(item.created_at).toLocaleDateString("ru-RU")}</span>
                  <span>{item.target_student_name ? `Для: ${item.target_student_name}` : "Для всех учеников"}</span>
                  <span>{item.submissions.length} ответов</span>
                </div>
              </div>
              <span className="pill">{item.submissions.length}</span>
            </button>
          ))}
        </div>
      </aside>
      <div className="stack">
        {activeHomework && (
          <article className="card homework-detail">
            <div className="homework-head">
              <div>
                <h3 style={{ margin: "0 0 8px" }}>{activeHomework.title}</h3>
                <div className="meta">
                  <span>{new Date(activeHomework.created_at).toLocaleDateString("ru-RU")}</span>
                  <span>{activeHomework.target_student_name ? `Для ученика: ${activeHomework.target_student_name}` : "Общее задание для всех прикрепленных учеников"}</span>
                  <span>{activeHomework.submissions.length} ответов</span>
                </div>
              </div>
              <span className="pill">{activeHomework.attachment_file_name ? "С вложением" : "Без вложения"}</span>
            </div>
            <p>{activeHomework.description}</p>
            {activeHomework.attachment_file_url && activeHomework.is_image && (
              <button
                className="homework-image-button"
                type="button"
                onClick={() => setLightboxImage({ src: activeHomework.attachment_file_url, alt: activeHomework.attachment_file_name || activeHomework.title })}
              >
                <img className="homework-preview-image" src={activeHomework.attachment_file_url} alt={activeHomework.attachment_file_name || activeHomework.title} />
              </button>
            )}
            {activeHomework.attachment_file_url && !activeHomework.is_image && (
              <a className="chat-file-link" href={activeHomework.attachment_file_url} target="_blank" rel="noreferrer" download={activeHomework.attachment_file_name}>
                <div className="attach-note">
                  <Paperclip size={14} />
                  <span>{activeHomework.attachment_file_name}</span>
                </div>
                <span className="chat-file-action">
                  <Download size={14} />
                  Скачать задание
                </span>
              </a>
            )}
          </article>
        )}

        <article className="card">
          <h3 style={{ marginTop: 0 }}>Новое задание</h3>
          <form className="form" onSubmit={createHomework}>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Тема задания" />
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание и требования" />
            <div className="stack">
              <label className="field-label">Кому назначить</label>
              <select value={targetStudentId} onChange={(event) => setTargetStudentId(event.target.value)}>
                <option value="">Всем прикрепленным ученикам</option>
                {students.map((student) => (
                  <option key={student.student_id} value={student.student_id}>{student.full_name}</option>
                ))}
              </select>
            </div>
            <label className="file-picker">
              <input className="file-picker-input" type="file" accept="image/*,.pdf,.doc,.docx" onChange={(event) => setAttachmentFile(event.target.files?.[0] || null)} />
              <span className="small-btn">
                <Paperclip size={14} />
                Выбрать файл
              </span>
              <span className="file-picker-name">{attachmentFile?.name || "Файл не выбран"}</span>
            </label>
            {attachmentFile && (
              <div className="attach-note">
                <Paperclip size={14} />
                <span>{attachmentFile.name}</span>
              </div>
            )}
            <button className="primary" type="submit">Опубликовать</button>
            {message && <div className="notice">{message}</div>}
          </form>
        </article>

        {activeHomework && (
          <article className="card">
            <div className="section-title">
              <h3>Ответы учеников</h3>
              <span className="pill">{activeHomework.submissions.length}</span>
            </div>
            <div className="stack">
              {activeHomework.submissions.length === 0 ? (
                <div className="empty">Пока никто не отправил ответ на это задание.</div>
              ) : activeHomework.submissions.map((submission) => {
                const draft = reviewDrafts[submission.id] || {
                  grade: submission.grade || 5,
                  teacher_comment: submission.teacher_comment || ""
                };
                return (
                  <article key={submission.id} className="card homework-submission-card">
                    <div className="homework-head">
                      <div>
                        <h4>{submission.student_name}</h4>
                        <div className="meta">
                          <span>{new Date(submission.created_at).toLocaleString("ru-RU")}</span>
                          <span>{submission.grade ? `Оценка ${submission.grade}/5` : "Ожидает оценивания"}</span>
                        </div>
                      </div>
                    </div>
                    <div className="review-summary">
                      <div className="account-mini-card">
                        <strong>Статус</strong>
                        <span>{submission.grade ? `Проверено на ${submission.grade}/5` : "Ждет проверки преподавателя"}</span>
                      </div>
                      <div className="account-mini-card">
                        <strong>Рецензия</strong>
                        <span>{submission.teacher_comment || "Пока без комментария"}</span>
                      </div>
                    </div>
                    {submission.is_image ? (
                      <button
                        className="homework-image-button"
                        type="button"
                        onClick={() => setLightboxImage({ src: submission.file_url, alt: submission.file_name })}
                      >
                        <img className="homework-preview-image" src={submission.file_url} alt={submission.file_name} />
                      </button>
                    ) : (
                      <a className="chat-file-link" href={submission.file_url} target="_blank" rel="noreferrer" download={submission.file_name}>
                        <div className="attach-note">
                          <Paperclip size={14} />
                          <span>{submission.file_name}</span>
                        </div>
                        <span className="chat-file-action">
                          <Download size={14} />
                          Скачать ответ
                        </span>
                      </a>
                    )}
                    <div className="form review-form">
                      <label className="field-label">Оценка</label>
                      <select
                        value={draft.grade}
                        onChange={(event) =>
                          setReviewDrafts((current) => ({
                            ...current,
                            [submission.id]: {
                              ...draft,
                              grade: Number(event.target.value)
                            }
                          }))
                        }
                      >
                        {[5, 4, 3, 2, 1].map((value) => <option key={value} value={value}>{value} / 5</option>)}
                      </select>
                      <label className="field-label">Рецензия для ученика</label>
                      <textarea
                        value={draft.teacher_comment}
                        onChange={(event) =>
                          setReviewDrafts((current) => ({
                            ...current,
                            [submission.id]: {
                              ...draft,
                              teacher_comment: event.target.value
                            }
                          }))
                        }
                        placeholder="Комментарий для ученика"
                      />
                      <button className="primary" type="button" onClick={() => saveReview(submission)}>
                        Сохранить проверку
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </article>
        )}
        <ImageLightbox image={lightboxImage} onClose={() => setLightboxImage(null)} />
      </div>
    </section>
  );
}

function HomeworkArea({ role }) {
  if (role === "tutor") {
    return <TutorHomeworkArea />;
  }
  return <StudentHomeworkArea />;
}

function ChatArea({ currentUser }) {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [attachMenuOpen, setAttachMenuOpen] = useState(false);
  const messagesRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (!messagesRef.current) return;
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    messagesEndRef.current?.scrollIntoView({ block: "end" });
  };

  async function loadChats() {
    try {
      const data = await api("/chats");
      setChats(data);
      setActiveChatId((current) => current || data[0]?.id || null);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function loadMessages(chatId) {
    if (!chatId) {
      setMessages([]);
      return;
    }

    try {
      setMessages(await api(`/chats/${chatId}/messages`));
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadChats();
  }, []);

  useEffect(() => {
    loadMessages(activeChatId);
  }, [activeChatId]);

  useLayoutEffect(() => {
    const frameOne = requestAnimationFrame(scrollToBottom);
    const timeoutId = window.setTimeout(scrollToBottom, 120);

    return () => {
      cancelAnimationFrame(frameOne);
      window.clearTimeout(timeoutId);
    };
  }, [activeChatId, messages]);

  useEffect(() => {
    function closeAttachMenu(event) {
      if (!event.target.closest(".attach-menu")) {
        setAttachMenuOpen(false);
      }
    }

    window.addEventListener("click", closeAttachMenu);
    return () => window.removeEventListener("click", closeAttachMenu);
  }, []);

  const activeChat = chats.find((item) => item.id === activeChatId);

  async function sendMessage(event) {
    event.preventDefault();
    if (!activeChatId) {
      setMessage("Сначала выберите чат.");
      return;
    }

    try {
      let fileKey = null;
      if (file) {
        fileKey = await uploadFileWithPresign(file);
      }

      await api(`/chats/${activeChatId}/messages`, {
        method: "POST",
        body: {
          text,
          file_key: fileKey,
          file_name: file?.name || null
        }
      });

      setText("");
      setFile(null);
      setAttachMenuOpen(false);
      setMessage("Сообщение отправлено.");
      await loadMessages(activeChatId);
      await loadChats();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="chat-shell">
      <aside className="card chat-list">
        <div className="section-title">
          <h3>Чаты</h3>
          <span className="pill">{chats.length}</span>
        </div>
        {chats.length === 0 ? (
          <div className="empty">Чаты появятся после прикрепления ученика к учителю.</div>
        ) : (
          <div className="stack">
            {chats.map((chat) => (
              <button
                key={chat.id}
                className={`chat-item ${activeChatId === chat.id ? "active" : ""}`}
                type="button"
                onClick={() => setActiveChatId(chat.id)}
              >
                <AvatarBadge user={{ avatar_url: chat.partner_avatar_url }} label={chat.partner_name} className="chat-list-avatar" />
                <div>
                  <strong>{chat.partner_name}</strong>
                  <div className="meta">
                    {chat.subject && <span>{chat.subject}</span>}
                  </div>
                  <p>{chat.last_message_text || chat.last_message_file_name || "Диалог уже готов к общению"}</p>
                </div>
              </button>
            ))}
          </div>
        )}
      </aside>

      <div className="card chat-thread">
        {activeChat ? (
          <>
            <div className="chat-thread-head">
              <div className="chat-thread-profile">
                <AvatarBadge user={{ avatar_url: activeChat.partner_avatar_url }} label={activeChat.partner_name} className="chat-head-avatar" />
                <div>
                  <h3 style={{ margin: 0 }}>{activeChat.partner_name}</h3>
                  <div className="meta">
                    {activeChat.subject && <span>{activeChat.subject}</span>}
                  </div>
                </div>
              </div>
            </div>
            <div ref={messagesRef} className="chat-messages">
              {messages.length === 0 ? (
                <div className="empty">Напишите первое сообщение в этом чате.</div>
              ) : messages.map((item) => (
                <div key={item.id} className={`chat-message-row ${item.sender_id === currentUser.id ? "mine" : ""}`}>
                  <AvatarBadge user={{ avatar_url: item.sender_avatar_url }} label={item.sender_name} className="chat-bubble-avatar" />
                  <article className={`chat-bubble ${item.sender_id === currentUser.id ? "mine" : ""}`}>
                    <div className="chat-bubble-author">{item.sender_name}</div>
                    {item.text && <p>{item.text}</p>}
                    {isPreviewableImage(item) && (
                      <a className="chat-image-link" href={item.file_url} target="_blank" rel="noreferrer">
                        <img className="chat-image" src={item.file_url} alt={item.file_name || "Изображение из чата"} onLoad={scrollToBottom} />
                      </a>
                    )}
                    {item.file_name && !isPreviewableImage(item) && item.file_url && (
                      <a className="chat-file-link" href={item.file_url} target="_blank" rel="noreferrer" download={item.file_name}>
                        <div className="attach-note">
                          <Paperclip size={14} />
                          <span>{item.file_name}</span>
                        </div>
                        <span className="chat-file-action">
                          <Download size={14} />
                          Скачать
                        </span>
                      </a>
                    )}
                    <time>{new Date(item.created_at).toLocaleString("ru-RU")}</time>
                  </article>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <form className="chat-compose" onSubmit={sendMessage}>
              <div className="chat-compose-row">
                <textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Напишите сообщение" />
                <div className="attach-menu">
                  <button
                    className={`icon-btn ${attachMenuOpen ? "active" : ""}`}
                    type="button"
                    aria-label="Вложения"
                    onClick={() => setAttachMenuOpen((value) => !value)}
                  >
                    <Paperclip size={17} />
                  </button>
                  <div className="attach-menu-popover" hidden={!attachMenuOpen}>
                    <label className="attach-action">
                      <input
                        type="file"
                        hidden
                        onChange={(event) => {
                          setFile(event.target.files?.[0] || null);
                          setAttachMenuOpen(false);
                        }}
                      />
                      <Paperclip size={15} />
                      <span>Прикрепить файл</span>
                    </label>
                    {file && (
                      <button className="attach-action danger" type="button" onClick={() => setFile(null)}>
                        <X size={15} />
                        <span>Убрать вложение</span>
                      </button>
                    )}
                  </div>
                </div>
                <button className="primary" type="submit">
                  <Send size={16} />
                  Отправить
                </button>
              </div>
              {file && (
                <div className="attach-note">
                  <Paperclip size={14} />
                  <span>{file.name}</span>
                </div>
              )}
              {message && <div className="notice">{message}</div>}
            </form>
          </>
        ) : (
          <div className="empty">Выберите чат слева, чтобы открыть переписку.</div>
        )}
      </div>
    </section>
  );
}

function WebinarsArea({ role }) {
  const items = role === "tutor"
    ? [
        { title: "Разбор варианта ЕГЭ", type: "Открытый эфир", meta: "45 минут", text: "Быстрый разбор сложных задач с возможностью потом прикрепить домашнюю работу." },
        { title: "Короткий видеоурок", type: "Запись", meta: "12 минут", text: "Небольшой материал по одной теме, который можно выдать ученикам до занятия." },
        { title: "Повторение перед пробником", type: "Интенсив", meta: "60 минут", text: "Формат для группы или потока, когда нужно быстро собрать учеников перед тестом." }
      ]
    : [
        { title: "Разбор варианта ЕГЭ", type: "Ближайший эфир", meta: "Сегодня в 19:00", text: "Можно заранее посмотреть тему, подключиться к эфиру и потом вернуться к записи." },
        { title: "Видеоурок по теме", type: "Запись", meta: "14 минут", text: "Короткие уроки подойдут для повторения между занятиями и перед домашней работой." },
        { title: "Интенсив перед пробником", type: "Подборка", meta: "3 записи", text: "Собранный блок с быстрыми объяснениями, полезными файлами и разбором ошибок." }
      ];

  return (
    <section className="stack">
      <div className="section-title">
        <h3>Видеоуроки и вебинары</h3>
        <span className="pill">{role === "tutor" ? "Эфиры и записи" : "Ближайшие материалы"}</span>
      </div>
      <div className="card webinar-hero">
        <div className="stack">
          <h3 style={{ margin: 0 }}>{role === "tutor" ? "Соберите библиотеку уроков и эфиров" : "Все эфиры и короткие уроки в одном месте"}</h3>
          <p className="summary" style={{ maxWidth: "100%" }}>
            {role === "tutor"
              ? "Здесь удобно размещать разборы тем, короткие записи и ближайшие живые занятия, чтобы ученики не теряли материалы."
              : "Здесь можно быстро открыть запись, посмотреть ближайший эфир и не искать полезные уроки по разным чатам."}
          </p>
        </div>
      </div>
      <div className="webinar-grid">
        {items.map((item) => (
          <article key={item.title} className="card webinar-card">
            <div className="meta">
              <span>{item.type}</span>
              <span>{item.meta}</span>
            </div>
            <h4>{item.title}</h4>
            <p>{item.text}</p>
            <button className="small-btn" type="button">{role === "tutor" ? "Подготовить материал" : "Открыть материал"}</button>
          </article>
        ))}
      </div>
    </section>
  );
}

function Leaderboard() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    api("/homework/leaderboard").then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <section>
      <div className="section-title">
        <h3>Лидерборд по оценкам</h3>
        <span className="pill">{items.length} учеников</span>
      </div>
      <div className="leaderboard">
        {items.length === 0 ? (
          <div className="empty">Пока нет проверенных работ для рейтинга.</div>
        ) : items.map((item, index) => (
          <article className="card leader-row" key={item.student_id}>
            <div className="rank-badge">{index + 1}</div>
            <div className="leader-main">
              <h4 style={{ margin: "0 0 4px" }}>{item.full_name}</h4>
              <div className="meta">
                <span>{item.graded_count} {pluralizeRussian(item.graded_count, "проверенная работа", "проверенные работы", "проверенных работ")}</span>
                <span>средняя оценка {item.average_grade}</span>
              </div>
              <div className="leader-stats">
                <div className="percent-bar compact">
                  <span style={{ width: `${Math.min((item.average_grade / 5) * 100, 100)}%` }} />
                </div>
              </div>
            </div>
            <div className="leader-score">
              <strong>{item.average_grade}</strong>
              <span>/ 5</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function UserShell({ currentUser, tab, setTab, dark, setDark, onLogout, onProfileUpdated }) {
  const isTutor = currentUser.role === "tutor";
  const [selectedTutorId, setSelectedTutorId] = useState(null);

  const content = useMemo(() => {
    if (tab === "home") return <HomeOverview currentUser={currentUser} onOpenPrimary={setTab} />;
    if (tab === "profile") return <PersonalAccount currentUser={currentUser} onProfileUpdated={onProfileUpdated} />;
    if (tab === "tutor-profile" && selectedTutorId) {
      return (
        <TutorProfilePage
          tutorId={selectedTutorId}
          currentUser={currentUser}
          onBack={() => {
            setSelectedTutorId(null);
            setTab("catalog");
          }}
          onEnroll={async (tutorId, isEnrolled) => {
            const result = await api(`/tutors/${tutorId}/enroll`, {
              method: isEnrolled ? "DELETE" : "POST"
            });
            return result;
          }}
        />
      );
    }
    if (tab === "offer") return <TutorOffer />;
    if (tab === "students") return <TutorStudentsArea />;
    if (tab === "homework") return <HomeworkArea role={currentUser.role} />;
    if (tab === "chats") return <ChatArea currentUser={currentUser} />;
    if (tab === "leaderboard") return <Leaderboard />;
    if (tab === "webinars") return <WebinarsArea role={currentUser.role} />;
    return <TutorsCatalog onOpenProfile={(tutorId) => {
      setSelectedTutorId(tutorId);
      setTab("tutor-profile");
    }} />;
  }, [currentUser, onProfileUpdated, selectedTutorId, tab, setTab]);

  const pageMeta = {
    home: {
      eyebrow: "Главная",
      title: "ПлюсБаллы",
      summary: "Онлайн-школа для спокойной учебы, общения с преподавателями и работы в одном кабинете."
    },
    catalog: {
      eyebrow: "Каталог",
      title: "Репетиторы по предметам",
      summary: "Сравните преподавателей и выберите подходящий формат занятий."
    },
    offer: {
      eyebrow: "Предложение",
      title: "Ваше предложение для учеников",
      summary: "Укажите предмет, цену и короткое описание занятий."
    },
    students: {
      eyebrow: "Ученики",
      title: "Все прикрепленные ученики",
      summary: "Следите за списком учеников и держите под рукой дату следующего занятия."
    },
    homework: {
      eyebrow: "Домашняя работа",
      title: isTutor ? "Задания для учеников" : "Мои задания",
      summary: isTutor
        ? "Публикуйте задания и следите за учебным процессом."
        : "Смотрите задания и отправляйте ответы файлами."
    },
    chats: {
      eyebrow: "Переписка",
      title: "Личные чаты с преподавателями",
      summary: "Здесь можно быстро обсуждать занятия, домашние задания и отправлять файлы."
    },
    "tutor-profile": {
      eyebrow: "Профиль репетитора",
      title: "О преподавателе",
      summary: "Рейтинг, отзывы и основная информация в одном месте."
    },
    profile: {
      eyebrow: "Личный кабинет",
      title: "Профиль и настройки",
      summary: "Управляйте профилем и основной информацией аккаунта."
    },
    leaderboard: {
      eyebrow: "Рейтинг",
      title: "Лидерборд по оценкам",
      summary: "Рейтинг строится по оценкам и числу проверенных работ."
    },
    webinars: {
      eyebrow: "Вебинары",
      title: "Живые занятия и эфиры",
      summary: "Здесь появятся ближайшие вебинары и записи."
    }
  };

  const meta = pageMeta[tab] || pageMeta.catalog;

  const navItems = isTutor
    ? [
        { id: "home", label: "Главная", icon: Home },
        { id: "profile", label: "Личный кабинет", icon: User },
        { id: "homework", label: "Задания", icon: GraduationCap },
        { id: "webinars", label: "Вебинары", icon: CalendarDays },
        { id: "chats", label: "Чаты", icon: MessageCircle },
        { id: "offer", label: "Предложение", icon: BookOpen },
        { id: "students", label: "Мои ученики", icon: Check },
        { id: "leaderboard", label: "Лидеры", icon: Trophy }
      ]
    : [
        { id: "home", label: "Главная", icon: Home },
        { id: "profile", label: "Личный кабинет", icon: User },
        { id: "homework", label: "Задания", icon: BookOpen },
        { id: "webinars", label: "Вебинары", icon: CalendarDays },
        { id: "chats", label: "Чаты", icon: MessageCircle },
        { id: "catalog", label: "Учителя", icon: GraduationCap },
        { id: "leaderboard", label: "Лидеры", icon: Trophy }
      ];

  return (
    <div className="shell">
      <aside className="sidebar">
        <Brand onClick={() => setTab("home")} />
        <nav className="nav" aria-label="Разделы">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={tab === item.id ? "active" : ""} type="button" onClick={() => setTab(item.id)}>
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="new-user">
          <div className="card" style={{ padding: 14 }}>
            <div className="eyebrow">{isTutor ? "Репетитор" : "Ученик"}</div>
            <div style={{ margin: "10px 0" }}>
              <AvatarBadge user={currentUser} label={currentUser.full_name} />
            </div>
            <h4 style={{ margin: "6px 0 4px" }}>{currentUser.full_name}</h4>
            <div className="meta">
              <span>{currentUser.email}</span>
            </div>
          </div>
          <button className="ghost" type="button" onClick={onLogout}>Выйти</button>
        </div>
      </aside>
      <main className={tab === "chats" ? "page-chat" : ""}>
        <header className={tab === "chats" ? "topbar topbar-compact" : "topbar"}>
          <div>
            <div className="eyebrow">{meta.eyebrow}</div>
            <h2>{meta.title}</h2>
            <p className="summary">{meta.summary}</p>
          </div>
        </header>
        {content}
      </main>
      <UtilityMenu
        dark={dark}
        onToggleTheme={() => setDark((value) => !value)}
        onOpenAdminLogin={() => {}}
        showAdminEntry={false}
      />
    </div>
  );
}

function App() {
  const [sessionType, setSessionType] = useState("guest");
  const [currentUser, setCurrentUser] = useState(null);
  const [tab, setTab] = useState("catalog");
  const [dark, setDark] = useState(localStorage.getItem("theme") === "dark");
  const [entryMode, setEntryMode] = useState("auth");
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    async function restoreSession() {
      if (!getToken()) {
        setBooting(false);
        return;
      }

      try {
        const me = await api("/auth/me");
        setCurrentUser(me);
        setSessionType("user");
        setTab("home");
      } catch {
        logout();
        setSessionType("guest");
        setCurrentUser(null);
      } finally {
        setBooting(false);
      }
    }

    restoreSession();
  }, []);

  async function handleUserLogin() {
    const me = await api("/auth/me");
    setCurrentUser(me);
    setSessionType("user");
    setTab("home");
  }

  function handleLogout() {
    logout();
    setCurrentUser(null);
    setSessionType("guest");
    setEntryMode("auth");
    setTab("home");
  }

  if (booting) {
    return (
      <section className="auth-screen">
        <div className="auth-panel" style={{ gridColumn: "1 / -1" }}>
          <div className="auth-card">
            <h2>Загружаем платформу</h2>
            <p className="summary">Проверяем текущую сессию и поднимаем нужный кабинет.</p>
          </div>
        </div>
      </section>
    );
  }

  if (sessionType === "guest") {
    if (entryMode === "admin") {
      return (
        <>
          <UtilityMenu
            dark={dark}
            onToggleTheme={() => setDark((value) => !value)}
            onOpenAdminLogin={() => setEntryMode("admin")}
            showAdminEntry={false}
          />
          <AdminLogin
            onBack={() => setEntryMode("auth")}
            onSuccess={() => {
              setSessionType("admin");
              setEntryMode("auth");
            }}
          />
        </>
      );
    }

    return (
      <>
        <UtilityMenu
          dark={dark}
          onToggleTheme={() => setDark((value) => !value)}
          onOpenAdminLogin={() => setEntryMode("admin")}
        />
        <Auth onLoggedIn={handleUserLogin} />
      </>
    );
  }

  if (sessionType === "admin") {
    return <AdminShell dark={dark} setDark={setDark} onLogout={handleLogout} />;
  }

  return (
    <UserShell
      currentUser={currentUser}
      tab={tab}
      setTab={setTab}
      dark={dark}
      setDark={setDark}
      onLogout={handleLogout}
      onProfileUpdated={setCurrentUser}
    />
  );
}

createRoot(document.getElementById("root")).render(<App />);







