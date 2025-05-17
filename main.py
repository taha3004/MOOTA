from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

S3, SUBJECTS = range(2)
user_marks = {}

ADMIN_ID = 8176170771

subjects_info = [
    ("Physics", 4, False),
    ("Analyse", 3, False),
    ("Informatics", 3, False),
    ("Rational Mechanics", 3, False),
    ("Analyse Num", 3, False),
    ("Chemistry", 3, False),
    ("Electronic", 3, False),
    ("Engineering", 3, False),
    ("Français", 1, True),
    ("English", 1, True)
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في ENR Rank!\n"
        "🧮 أرسل /calculate لحساب المعدل.\n"
        "🛠 أرسل /reset لمسح البيانات (للمطور فقط)."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        user_marks.clear()
        await update.message.reply_text("✅ تم مسح جميع البيانات.")
    else:
        await update.message.reply_text("🚫 لا تملك صلاحية تنفيذ هذا الأمر.")

def input_float(text):
    try:
        val = float(text)
        if 0 <= val <= 20:
            return val
    except:
        return None

def calculate_subject_mark(cc, exam, is_full_exam=False):
    return exam if is_full_exam else (0.5 * cc + 0.5 * exam)

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 أدخل معدل الفصل الثالث (S3):")
    return S3

async def s3_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = input_float(update.message.text)
    if val is None:
        await update.message.reply_text("❌ أدخل رقم بين 0 و 20.")
        return S3
    context.user_data['s3'] = val
    context.user_data['subject_index'] = 0
    context.user_data['marks'] = []
    subj = subjects_info[0][0]
    await update.message.reply_text(f"{subj} - أدخل التقييم المستمر (CC):")
    return SUBJECTS

async def subjects_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data['subject_index']
    subj, coeff, full_exam = subjects_info[idx]

    val = input_float(update.message.text)
    if val is None:
        await update.message.reply_text("❌ أدخل رقم صحيح.")
        return SUBJECTS

    if 'cc' not in context.user_data:
        if full_exam:
            context.user_data['marks'].append(val)
            context.user_data['subject_index'] += 1
            return await next_subject(update, context)
        else:
            context.user_data['cc'] = val
            await update.message.reply_text(f"{subj} - أدخل الامتحان (Exam):")
            return SUBJECTS
    else:
        cc = context.user_data.pop('cc')
        mark = calculate_subject_mark(cc, val)
        context.user_data['marks'].append(mark)
        context.user_data['subject_index'] += 1
        return await next_subject(update, context)

async def next_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data['subject_index']
    if idx >= len(subjects_info):
        s3 = context.user_data['s3']
        s4_num = 0
        s4_den = 0
        for i, (_, coeff, _) in enumerate(subjects_info):
            s4_num += context.user_data['marks'][i] * coeff
            s4_den += coeff
        s4 = s4_num / s4_den
        final = (s3 + s4) / 2

        uid = update.message.from_user.id
        user_marks[uid] = final

        sorted_all = sorted(user_marks.values(), reverse=True)
        rank = sorted_all.index(final) + 1
        total = len(sorted_all)

        if rank <= 96:
            status = "🎉 قبول مباشر"
        elif final >= 9.5:
            status = "✅ مؤهل للمسابقة (24 منصب)"
        else:
            status = "❌ غير مؤهل"

        await update.message.reply_text(
            f"📊 الفصل الرابع (S4): {s4:.2f}\n"
            f"📊 المعدل النهائي: {final:.2f}\n"
            f"📈 ترتيبك: {rank} من {total}\n\n{status}"
        )
        return ConversationHandler.END
    else:
        subj, _, full_exam = subjects_info[idx]
        msg = f"{subj} - أدخل الامتحان:" if full_exam else f"{subj} - أدخل التقييم المستمر (CC):"
        await update.message.reply_text(msg)
        return SUBJECTS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

if __name__ == '__main__':
    import os
    import asyncio

    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ ضع التوكن كمتغير بيئة TELEGRAM_TOKEN.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("calculate", calculate)],
        states={
            S3: [MessageHandler(filters.TEXT & ~filters.COMMAND, s3_received)],
            SUBJECTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, subjects_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(conv)

    print("✅ البوت يعمل الآن...")

    asyncio.get_event_loop().run_until_complete(app.run_polling())
