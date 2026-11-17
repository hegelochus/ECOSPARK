# EcoSpark – „Чувари на природата“ (Streamlit + Supabase + Google sign-in)
import csv
import io
import uuid
from datetime import datetime

import streamlit as st
from PIL import Image, ImageOps
from supabase import create_client

st.set_page_config(page_title="EcoSpark – Чувари на природата", page_icon="🌱")


def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return default


ADMIN_EMAIL = str(secret("ADMIN_EMAIL", "josif.zoev123@gmail.com")).strip().lower()
TERMS_VERSION = "2026-11-17"  # change this to make every user accept the terms again
BUCKET = "post-images"
MAX_IMAGES, MAX_MB = 3, 5

CHARACTERS = [
    ("🌳", "Дарко", "уништувањето на шумата"),
    ("🐧", "Пако", "промените во ледената средина"),
    ("🐘", "Ела", "недостигот од вода"),
    ("🐬", "Димче", "подводната бучава"),
    ("🦅", "Гордан", "промените во воздушните струења"),
    ("🌸", "Ирис", "нарушувањето на природниот циклус на цветање"),
]

TERMS_MD = f"""
**Верзија {TERMS_VERSION}**

Овие услови важат за користење на веб-платформата EcoSpark – „Чувари на природата“ („платформата“).
Со пријавување и прифаќање на условите се согласувате со следново.

### 1. Платформата
Платформата е заедница околу еко-предизвиците од нашите сликовници. Секој може да ја чита.
Објавување и коментирање е дозволено само за пријавени корисници што ги прифатиле овие услови.
Само администраторот објавува новости на страницата „Заедница – Новости“.

### 2. Возраст и деца
Профил може да креирате ако имате 18 или повеќе години. Деца може да учествуваат само преку
родител, старател или наставник. Не објавувајте лични податоци на деца (презиме, адреса, училиште)
и не објавувајте препознатливи фотографии на деца ако немате согласност од нивниот родител или старател.

### 3. Вашата содржина и лиценца за маркетинг
Авторските права над текстовите и фотографиите што ги објавувате остануваат ваши.
Со објавувањето ни давате неексклузивна, бесплатна, светска лиценца да ја користиме,
умножуваме, прилагодуваме (на пример, сечење или скратување) и прикажуваме содржината
во маркетингот и промоцијата на EcoSpark: веб-страница, социјални мрежи, презентации,
печатени и дигитални материјали. Каде е можно, ќе го наведуваме вашето име.
Потврдувате дека имате право да ја објавите содржината и дека на сликите
нема деца без согласност на нивниот родител или старател.

### 4. Податоци што ги собираме
Од вашиот Google профил добиваме име и е-пошта. Чуваме и што објавувате и коментирате,
како и датумот на прифаќање на овие услови. Користиме податоци за работа на платформата,
комуникација со вас, статистика и развој на EcoSpark. Фотографиите се намалуваат и се
чистат од скриени метаподатоци (на пример, GPS локација) пред да се зачуваат.

### 5. База на корисници и можна продажба на EcoSpark
Ги чуваме податоците за корисниците во база на корисници. Ако EcoSpark се спои, продаде
или добие инвеститор, можеме да ја прикажеме базата (или дел од неа, по можност збирно или
анонимно) на потенцијални купувачи, инвеститори и партнери за да ја проценат вредноста
на бизнисот. Ќе споделуваме само што е потребно и под обврска за доверливост. Купувачот
мора да ги почитува овие услови. Не ги продаваме вашите податоци одделно на трети лица
за нивни сопствени маркетиншки цели.

### 6. Ваши права
Можете да побарате пристап, исправка или бришење на вашите податоци и да ја повлечете
согласноста. Во менито лево има копче „Избриши ги моите податоци“ што ги брише вашиот
профил, објавите, коментарите и сликите. Материјали што веќе се објавени или печатени
пред бришењето не мора да се повлечат. За други барања пишете ни на **{ADMIN_EMAIL}**.

### 7. Правила на однесување
Забрането е навредливо, дискриминаторско, незаконско или спам или непожелна реклама и
содржина што му штети на дете. Администраторот може да избрише содржина што не ги почитува
правилата.

### 8. Промени
Ако ги променим условите, ќе побараме повторно да ги прифатите пред да продолжите
да објавувате или коментирате.
"""


# ------------------------------------------------------------------ helpers
@st.cache_resource
def _client():
    url, key = secret("SUPABASE_URL"), secret("SUPABASE_SERVICE_KEY")
    if not url or not key:
        st.error("Недостасуваат SUPABASE_URL и SUPABASE_SERVICE_KEY во secrets.")
        st.stop()
    return create_client(url, key)


def db():
    return _client()


def fmt(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(ts)[:10]


def current():
    """The signed-in Google user, or None."""
    if not getattr(st.user, "is_logged_in", False):
        return None
    email = (getattr(st.user, "email", "") or "").strip().lower()
    if not email:
        return None
    name = getattr(st.user, "name", "") or email.split("@")[0]
    return {"email": email, "name": name, "verified": getattr(st.user, "email_verified", True)}


def is_admin(u=None):
    u = u or current()
    return bool(u and u["email"] == ADMIN_EMAIL and u["verified"] is not False)


def accepted(u):
    key = f"acc_{u['email']}_{TERMS_VERSION}"
    if st.session_state.get(key):
        return True
    rows = db().table("profiles").select("terms_version").eq("email", u["email"]).limit(1).execute().data
    ok = bool(rows and rows[0].get("terms_version") == TERMS_VERSION)
    if ok:
        st.session_state[key] = True
    return ok


def member():
    u = current()
    return u if (u and accepted(u)) else None


def flash(msg=None):
    if msg:
        st.session_state["_flash"] = msg
    elif st.session_state.get("_flash"):
        st.success(st.session_state.pop("_flash"))


def member_gate(action_text, key):
    """Return the member, or show the right prompt (sign in / accept terms)."""
    u = current()
    if not u:
        st.info(f"Најавете се за да {action_text}.")
        st.button("Најави се со Google", on_click=st.login, key=f"login_{key}")
        return None
    if accepted(u):
        return u
    st.warning("Пред да објавувате или коментирате, прифатете ги Условите за користење.")
    with st.expander("Прочитај ги условите"):
        st.markdown(TERMS_MD)
    ok = st.checkbox(
        "Ги прочитав и ги прифаќам Условите, вклучувајќи ја лиценцата за маркетинг и чувањето "
        "на моите податоци во база на корисници.",
        key=f"terms_ok_{key}",
    )
    if st.button("Продолжи", type="primary", disabled=not ok, key=f"terms_btn_{key}"):
        db().table("profiles").upsert(
            {
                "email": u["email"],
                "name": u["name"],
                "terms_version": TERMS_VERSION,
                "terms_accepted_at": datetime.utcnow().isoformat(),
            }
        ).execute()
        st.session_state[f"acc_{u['email']}_{TERMS_VERSION}"] = True
        st.rerun()
    return None


def prepare_image(f):
    img = ImageOps.exif_transpose(Image.open(f)).convert("RGB")  # re-saving drops EXIF/GPS
    img.thumbnail((1400, 1400))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82)
    return buf.getvalue()


def image_urls(paths):
    return [db().storage.from_(BUCKET).get_public_url(p).rstrip("?") for p in (paths or [])]


# --------------------------------------------------------- admin-only deletes
def _run_delete(confirm_key, action, *args):
    if is_admin():  # always re-check on the server before deleting
        try:
            action(*args)
            flash("Избришано.")
        except Exception as e:
            st.session_state["_err"] = f"Бришењето не успеа: {e}"
    st.session_state[confirm_key] = False


def delete_button(key, action, *args):
    """Two-step delete using Streamlit state (no browser pop-ups)."""
    if not is_admin():
        return
    ck = f"confirm_{key}"
    if st.session_state.get(ck):
        c1, c2, _ = st.columns([2, 1, 3])
        c1.button("Потврди бришење", key=f"yes_{key}", type="primary",
                  on_click=_run_delete, args=(ck, action, *args))
        c2.button("Откажи", key=f"no_{key}", on_click=st.session_state.update, args=({ck: False},))
    else:
        st.button("🗑 Избриши", key=f"del_{key}", on_click=st.session_state.update, args=({ck: True},))


def delete_post(post_id, paths):
    if paths:
        db().storage.from_(BUCKET).remove(paths)
    db().table("posts").delete().eq("id", post_id).execute()  # comments cascade


def delete_comment(cid):
    db().table("comments").delete().eq("id", cid).execute()


def delete_news(nid):
    db().table("news").delete().eq("id", nid).execute()


def delete_my_data(email):
    u = current()
    if not u or u["email"] != email:
        return
    posts = db().table("posts").select("id,image_paths").eq("author_email", email).execute().data
    paths = [p for row in posts for p in (row.get("image_paths") or [])]
    if paths:
        db().storage.from_(BUCKET).remove(paths)
    db().table("comments").delete().eq("author_email", email).execute()
    db().table("posts").delete().eq("author_email", email).execute()
    db().table("profiles").delete().eq("email", email).execute()
    flash("Вашите податоци се избришани.")


# ---------------------------------------------------------------------- pages
def page_who():
    st.title("Не чекај да пораснеш за да ја чуваш планетата.")
    st.subheader("Стани нејзин чувар уште денес!")
    st.write(
        "EcoSpark е серија од шест илустрирани едукативни сликовници за деца од 5 до 10 години. "
        "Шест животински и растителни ликови ги раскажуваат последиците од климатските промени "
        "и загадувањето, а секоја сликовница завршува со практичен Еко-предизвик."
    )
    cols = st.columns(3)
    for i, (emoji, name, _) in enumerate(CHARACTERS):
        cols[i % 3].markdown(f"### {emoji} {name}")
    st.header("Јазот помеѓу знаењето и желбата да се дејствува")
    st.write(
        "Децата сè почесто слушаат за климатските промени, загадувањето и загрозените видови. "
        "Но кога проблемот изгледа далечен и преголем, лесно се создава чувство дека едно дете "
        "не може да направи ништо. Природата е нашиот дом, а нејзината иднина зависи од "
        "секојдневните избори. Нашата цел не е да ги исплашиме децата, туку да развиеме "
        "емпатија, еколошка свест и чувство дека се дел од решението."
    )
    st.header("Нашиот пристап")
    a, b, c = st.columns(3)
    a.markdown("**Почувствуј**\n\nДетето добива лик со кој се поврзува и го доживува неговиот страв, жед или загриженост.")
    b.markdown("**Разбери**\n\nПреку приказната ги открива причините и последиците на еколошкиот проблем.")
    c.markdown("**Дејствувај**\n\nСекоја сликовница завршува со практичен Еко-предизвик за секојдневниот живот.")
    st.write(
        "На крајот од секоја сликовница ќе има QR-код што го води детето до конкретен "
        "Еко-предизвик, кој може доброволно да го изведе со поддршка од родител или наставник. "
        "Во страницата „Еко предизвици“ споделуваме што сме направиле за природата."
    )


def page_products():
    st.title("Колекцијата „Чувари на природата“")
    st.write("Шест сликовници, шест еколошки проблеми, шест ликови. Секоја завршува со Еко-предизвик.")
    for i in range(0, 6, 3):
        cols = st.columns(3)
        for col, (emoji, name, topic) in zip(cols, CHARACTERS[i:i + 3]):
            with col.container(border=True):
                st.markdown(f"## {emoji}")
                st.markdown(f"**{name}**")
                st.caption(f"Приказна за {topic}.")
    st.header("Цени")
    c1, c2 = st.columns(2)
    c1.metric("Една сликовница", "200 денари")
    c2.metric("Комплет од шест", "1.200 денари")
    st.write("Во комплетот: специјално изработена EcoSpark боенка гратис.")
    st.caption("Предложени цени. Конечните цени ќе се утврдат по понудите од печатниците.")
    st.header("Каде ќе се продава")
    st.markdown(
        "- **Родители и семејства:** онлајн, преку Facebook, Instagram и TikTok и во книжарници.\n"
        "- **Книжарници:** поединечни сликовници и комплети преку дистрибутери.\n"
        "- **Градинки и училишта:** дополнителен материјал за еколошко образование.\n"
        "- **Компании:** едукативни новогодишни подароци; количински цени за поголеми нарачки."
    )


def page_challenges():
    st.title("Еко предизвици")
    st.write("Простор каде споделуваме еко-предизвици, фотографии и идеи.")
    flash()
    if st.session_state.get("_err"):
        st.error(st.session_state.pop("_err"))

    u = member_gate("споделите еко-предизвик и да коментирате", "blog")
    if u:
        with st.form("new_post", clear_on_submit=True):
            st.subheader("Сподели го твојот еко-предизвик")
            title = st.text_input("Наслов", max_chars=120)
            body = st.text_area("Што направи за природата?", max_chars=2000, height=140)
            files = st.file_uploader(f"Фотографии (најмногу {MAX_IMAGES})",
                                     type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
            ok = st.checkbox("Потврдувам дека имам право да ја објавам содржината и дека на сликите "
                             "нема деца без согласност на родител или старател.")
            go = st.form_submit_button("Објави", type="primary")
        if go:
            if not title.strip() or not body.strip():
                st.error("Внесете наслов и опис.")
            elif not ok:
                st.error("Потврдете го полето пред објавување.")
            elif len(files) > MAX_IMAGES or any(f.size > MAX_MB * 1024 * 1024 for f in files):
                st.error(f"Најмногу {MAX_IMAGES} слики, секоја до {MAX_MB} MB.")
            else:
                uploaded = []
                try:
                    for f in files:
                        path = f"{uuid.uuid4().hex}.jpg"
                        db().storage.from_(BUCKET).upload(path, prepare_image(f), {"content-type": "image/jpeg"})
                        uploaded.append(path)
                    db().table("posts").insert({
                        "author_email": u["email"], "author_name": u["name"],
                        "title": title.strip(), "body": body.strip(), "image_paths": uploaded,
                    }).execute()
                    flash("Објавено! Благодариме што го чуваш природата.")
                    st.rerun()
                except Exception as e:
                    if uploaded:
                        db().storage.from_(BUCKET).remove(uploaded)
                    st.error(f"Објавата не успеа: {e}")

    posts = db().table("posts").select("*").order("created_at", desc=True).limit(50).execute().data
    if not posts:
        st.info("Сè уште нема објави. Биди првиот што ќе сподели еко-предизвик!")
        return
    ids = [p["id"] for p in posts]
    comments = db().table("comments").select("*").in_("post_id", ids).order("created_at").execute().data
    for p in posts:
        with st.container(border=True):
            st.subheader(p["title"])
            badge = " · Админ" if p["author_email"] == ADMIN_EMAIL else ""
            st.caption(f"{p['author_name']}{badge} · {fmt(p['created_at'])}")
            st.write(p["body"])
            urls = image_urls(p.get("image_paths"))
            if urls:
                st.image(urls, width=260)
            delete_button(f"post_{p['id']}", delete_post, p["id"], p.get("image_paths") or [])
            mine = [c for c in comments if c["post_id"] == p["id"]]
            st.markdown(f"**Коментари ({len(mine)})**")
            for c in mine:
                st.markdown(f"**{c['author_name']}** · _{fmt(c['created_at'])}_")
                st.write(c["body"])
                delete_button(f"cm_{c['id']}", delete_comment, c["id"])
            if u:
                with st.form(f"cf_{p['id']}", clear_on_submit=True):
                    text = st.text_input("Коментар", max_chars=500, placeholder="Напиши коментар",
                                         label_visibility="collapsed")
                    sent = st.form_submit_button("Коментирај")
                if sent and text.strip():
                    db().table("comments").insert({
                        "post_id": p["id"], "author_email": u["email"],
                        "author_name": u["name"], "body": text.strip(),
                    }).execute()
                    st.rerun()


def page_news():
    st.title("Заедница – Новости")
    st.write("Најнови информации за компанијата и производите. Оваа страница е само за читање: "
             "новостите ги објавува администраторот.")
    flash()
    if st.session_state.get("_err"):
        st.error(st.session_state.pop("_err"))

    if is_admin():
        with st.form("new_news", clear_on_submit=True):
            st.subheader("Нова објава (само администратор)")
            title = st.text_input("Наслов", max_chars=150)
            body = st.text_area("Текст", height=160)
            link = st.text_input("Линк (по желба)", placeholder="https://")
            go = st.form_submit_button("Објави новост", type="primary")
        if go:
            if not title.strip() or not body.strip():
                st.error("Внесете наслов и текст.")
            else:
                db().table("news").insert({
                    "title": title.strip(), "body": body.strip(),
                    "link": link.strip() or None, "author_email": ADMIN_EMAIL,
                }).execute()
                flash("Новоста е објавена.")
                st.rerun()

    items = db().table("news").select("*").order("created_at", desc=True).limit(50).execute().data
    if not items:
        st.info("Сè уште нема новости. Следете не за ажурирања.")
    for n in items:
        with st.container(border=True):
            st.subheader(n["title"])
            st.caption(fmt(n["created_at"]))
            st.write(n["body"])
            if n.get("link") and str(n["link"]).startswith(("http://", "https://")):
                st.link_button("Повеќе", n["link"])
            delete_button(f"news_{n['id']}", delete_news, n["id"])


def page_terms():
    st.title("Услови за користење")
    st.markdown(TERMS_MD)


def page_admin():
    st.title("Админ")
    if not is_admin():
        st.error("Само администраторот има пристап.")
        return
    users = db().table("profiles").select("*").order("terms_accepted_at", desc=True).execute().data
    posts = db().table("posts").select("id", count="exact").limit(1).execute().count
    cms = db().table("comments").select("id", count="exact").limit(1).execute().count
    a, b, c = st.columns(3)
    a.metric("Корисници", len(users))
    b.metric("Објави", posts)
    c.metric("Коментари", cms)
    st.subheader("База на корисници")
    st.caption("Користете ја според Условите (точка 5): споделувајте само што е потребно, "
               "по можност збирно или анонимно, и под обврска за доверливост.")
    st.dataframe(users, use_container_width=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["email", "name", "terms_version", "terms_accepted_at", "created_at"],
                       extrasaction="ignore")
    w.writeheader()
    w.writerows(users)
    st.download_button("Преземи CSV", buf.getvalue().encode("utf-8-sig"), "ecospark-korisnici.csv", "text/csv")


# -------------------------------------------------------------------- sidebar
def sidebar():
    u = current()
    with st.sidebar:
        if not u:
            st.button("Најави се со Google", on_click=st.login, key="login_side")
            return
        st.markdown(f"👤 **{u['name']}**" + (" · Админ" if is_admin(u) else ""))
        st.caption(u["email"])
        st.button("Одјави се", on_click=st.logout, key="logout_side")
        with st.expander("Мои податоци"):
            st.caption("Ги брише вашиот профил, објавите, коментарите и сликите.")
            if st.session_state.get("confirm_mine"):
                st.button("Да, избриши сè", type="primary", key="mine_yes", on_click=_delete_mine, args=(u["email"],))
                st.button("Откажи", key="mine_no", on_click=st.session_state.update, args=({"confirm_mine": False},))
            else:
                st.button("Избриши ги моите податоци", key="mine_del",
                          on_click=st.session_state.update, args=({"confirm_mine": True},))


def _delete_mine(email):
    try:
        delete_my_data(email)
        st.session_state.pop(f"acc_{email}_{TERMS_VERSION}", None)
    except Exception as e:
        st.session_state["_err"] = f"Бришењето не успеа: {e}"
    st.session_state["confirm_mine"] = False


# ----------------------------------------------------------------------- main
pages = [
    st.Page(page_who, title="Кои сме ние", icon="🌱", url_path="who", default=True),
    st.Page(page_products, title="Нашите производи", icon="📚", url_path="products"),
    st.Page(page_challenges, title="Еко предизвици", icon="💬", url_path="challenges"),
    st.Page(page_news, title="Заедница – Новости", icon="📣", url_path="news"),
    st.Page(page_terms, title="Услови за користење", icon="📄", url_path="terms"),
]
if is_admin():
    pages.append(st.Page(page_admin, title="Админ", icon="🛠", url_path="admin"))

sidebar()
st.navigation(pages).run()
