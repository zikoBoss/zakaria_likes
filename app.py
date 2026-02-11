from flask import Flask, render_template, request, jsonify, session
import requests
import base64
import time
import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'zakaria-likes-secret-key-2026'

# نظام الحدود لكل UID
uid_requests = {}

def get_api_url(uid, server_name):
    """توليد رابط API"""
    try:
        d_url = base64.b64decode("aHR0cHM6Ly9kdXJhbnRvLWxpa2UtcGVhcmwudmVyY2VsLmFwcC9saWtlP3VpZD17dWlkfSZzZXJ2ZXJfbmFtZT17c2VydmVyX25hbWV9").decode()
        return d_url.format(uid=uid, server_name=server_name)
    except:
        return None

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/api/send_likes', methods=['POST'])
def send_likes():
    """إرسال طلب الإعجابات"""
    data = request.json
    uid = data.get('uid')
    server = data.get('server')
    
    if not uid or not uid.isdigit():
        return jsonify({
            'success': False,
            'message': '❌ يرجى إدخال UID صحيح'
        })
    
    # ⏳ التحقق من حدود الـ UID
    today = str(datetime.date.today())
    current_time = time.time()
    
    if uid not in uid_requests:
        uid_requests[uid] = {'date': today, 'count': 0, 'last_time': 0}
    else:
        if uid_requests[uid]['date'] != today:
            uid_requests[uid] = {'date': today, 'count': 0, 'last_time': uid_requests[uid]['last_time']}
    
    # التحقق من المهلة (دقيقة)
    if current_time - uid_requests[uid]['last_time'] < 60:
        remaining = int(60 - (current_time - uid_requests[uid]['last_time']))
        return jsonify({
            'success': False,
            'message': f'⏳ انتظر {remaining} ثانية قبل طلب جديد'
        })
    
    # التحقق من الحد اليومي (3 طلبات)
    if uid_requests[uid]['count'] >= 3:
        return jsonify({
            'success': False,
            'message': '❌ لقد استنفذت الحد اليومي (3 طلبات فقط)'
        })
    
    try:
        # استدعاء API
        api_url = get_api_url(uid, server)
        if not api_url:
            return jsonify({
                'success': False,
                'message': '❌ خطأ في النظام'
            })
        
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        # تحديث العداد
        uid_requests[uid]['count'] += 1
        uid_requests[uid]['last_time'] = current_time
        uid_requests[uid]['date'] = today
        
        # استخراج النتائج
        likes_given = data.get('LikesGivenByAPI', 0)
        likes_after = data.get('LikesafterCommand', 0)
        likes_before = data.get('LikesbeforeCommand', 0)
        player_nickname = data.get('PlayerNickname', 'غير معروف')
        status = data.get('status', 0)
        
        # أسماء المناطق
        region_names = {
            'me': 'الشرق الأوسط', 'eu': 'أوروبا', 'us': 'أمريكا الشمالية',
            'in': 'الهند', 'br': 'البرازيل', 'id': 'إندونيسيا',
            'tr': 'تركيا', 'th': 'تايلاند'
        }
        
        # أيقونات الحالة
        status_icons = {0: "❌ فشل", 1: "⚠️ محدود", 2: "✅ ناجح", 3: "🔒 مغلق"}
        
        # رسالة النجاح/الفشل
        if likes_given > 0:
            result_message = "✅ تمت الإضافة بنجاح"
        elif status == 2:
            result_message = "ℹ️ لقد استلمت الإعجابات مسبقاً"
        else:
            result_message = "❌ لم تتم الإضافة"
        
        # الطلبات المتبقية
        remaining_requests = 3 - uid_requests[uid]['count']
        
        return jsonify({
            'success': True,
            'player_name': player_nickname,
            'uid': uid,
            'region': region_names.get(server, server.upper()),
            'likes_before': likes_before,
            'likes_after': likes_after,
            'likes_added': likes_given,
            'status': status_icons.get(status, '❓'),
            'result_message': result_message,
            'remaining_requests': remaining_requests,
            'next_reset': 'غداً'
        })
        
    except requests.exceptions.RequestException:
        return jsonify({
            'success': False,
            'message': '❌ فشل الاتصال بالخادم'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ خطأ: {str(e)}'
        })

@app.route('/api/check_limits', methods=['POST'])
def check_limits():
    """التحقق من حدود UID"""
    data = request.json
    uid = data.get('uid')
    
    if uid in uid_requests:
        remaining = 3 - uid_requests[uid]['count']
        return jsonify({
            'remaining': remaining,
            'total_used': uid_requests[uid]['count']
        })
    else:
        return jsonify({
            'remaining': 3,
            'total_used': 0
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)