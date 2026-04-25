from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Follow, Message, ApplicantProfile, RecruiterProfile, HRProfile, UserSettings
from models import ApplicantNotification, RecruiterNotification, HRNotification, get_ph_time
from datetime import datetime
from sqlalchemy import or_, and_
from models import MessageReaction
import json

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


# =========================
# HELPERS
# =========================
def get_display_name(user):
    """Return full name from whichever profile type the user has."""
    if user.role == "applicant":
        p = ApplicantProfile.query.filter_by(user_id=user.id).first()
        if p and p.first_name:
            return f"{p.first_name} {p.last_name}".strip()
    elif user.role == "recruiter":
        p = RecruiterProfile.query.filter_by(user_id=user.id).first()
        if p and p.first_name:
            return f"{p.first_name} {p.surname}".strip()
    elif user.role == "hr":
        p = HRProfile.query.filter_by(user_id=user.id).first()
        if p and p.first_name:
            return f"{p.first_name} {p.last_name}".strip()
    return user.username


def get_company_name(user):
    """Return company name for recruiters / HR."""
    if user.role == "recruiter":
        p = RecruiterProfile.query.filter_by(user_id=user.id).first()
        return p.company_name if p else None
    if user.role == "hr":
        if user.created_by:
            recruiter = User.query.get(user.created_by)
            if recruiter:
                p = RecruiterProfile.query.filter_by(user_id=recruiter.id).first()
                return p.company_name if p else None
    return None


def get_user_settings(user_id):
    """
    Return UserSettings for a user with safe defaults if none exist.
    Returns a plain dict so the template/card can access fields easily.
    """
    s = UserSettings.query.filter_by(user_id=user_id).first()
    if not s:
        return {
            "show_name":       "everyone",
            "show_profile":    "everyone",
            "who_can_message": "all",
            "show_follow_list": "yes",
            "show_follow_count": "yes",
            "profile_audience": ["recruiter", "hr", "follower"],
        }

    try:
        audience = json.loads(s.profile_audience_json) if s.profile_audience_json else ["recruiter", "hr", "follower"]
    except Exception:
        audience = ["recruiter", "hr", "follower"]

    return {
        "show_name":        s.show_name        or "everyone",
        "show_profile":     s.show_profile     or "everyone",
        "who_can_message":  s.who_can_message  or "all",
        "show_follow_list": s.show_follow_list or "yes",
        "show_follow_count": s.show_follow_count or "yes",
        "profile_audience": audience,
    }


def is_mutual_follow(user_a_id, user_b_id):
    """True if both users follow each other."""
    if not user_a_id or not user_b_id:
        return False
    a_follows_b = Follow.query.filter_by(follower_id=user_a_id, followed_id=user_b_id).first()
    b_follows_a = Follow.query.filter_by(follower_id=user_b_id, followed_id=user_a_id).first()
    return bool(a_follows_b and b_follows_a)


def build_user_card(user, current_user_id=None, current_user_role=None, following_ids=None):
    """
    Return a dict with everything needed to render a user card,
    including privacy and messaging settings from UserSettings.
    """
    company = get_company_name(user)

    # ── Follow state ──
    is_following = user.id in following_ids if following_ids is not None else False
    if following_ids is None and current_user_id:
        is_following = Follow.query.filter_by(
            follower_id=current_user_id, followed_id=user.id
        ).first() is not None

    follower_count = Follow.query.filter_by(followed_id=user.id).count()

    # ── Mutual follow ──
    mutual = is_mutual_follow(current_user_id, user.id) if current_user_id else False

    # ── Privacy settings ──
    settings = get_user_settings(user.id)
    show_profile    = settings["show_profile"]
    who_can_message = settings["who_can_message"]
    show_name       = settings["show_name"]

    # ── Display name — respect show_name == 'mutual' ──
    full_name = get_display_name(user)
    if show_name == "mutual" and not mutual:
        display_name = user.username   # hide real name if not mutual
    else:
        display_name = full_name

    # ── Can the current viewer message this user? ──
    viewer_can_msg = True
    if who_can_message == "recruiters":
        if not (current_user_id and current_user_role == "recruiter"):
            viewer_can_msg = False
    elif who_can_message == "mutual":
        if not mutual:
            viewer_can_msg = False

    return {
        "id":              user.id,
        "username":        user.username,
        "display_name":    display_name,
        "role":            user.role,
        "company":         company,
        "profile_picture": user.profile_picture,
        "is_following":    is_following,
        "is_mutual":       mutual,
        "follower_count":  follower_count,
        # ── privacy fields (used by template badges) ──
        "show_profile":    show_profile,
        "who_can_message": who_can_message,
        "viewer_can_msg":  viewer_can_msg,
    }


def serialize_message(m, current_user_id, active_display_name=None):
    """
    Serialize a Message object to a dict for JSON responses.
    Includes reply_to fields needed by the JS appendBubble() function.
    """
    reply_to_body   = None
    reply_to_author = None

    if m.reply_to_id and m.reply_to:
        reply_to_body = m.reply_to.body
        if m.reply_to.sender_id == current_user_id:
            reply_to_author = "You"
        else:
            reply_to_author = active_display_name or "Them"

    return {
        "id":              m.id,
        "body":            m.body,
        "sender_id":       m.sender_id,
        "created_at":      m.created_at.strftime("%I:%M %p"),
        "is_mine":         m.sender_id == current_user_id,
        "edited":          m.edited,
        "reply_to_id":     m.reply_to_id,
        "reply_to_body":   reply_to_body,
        "reply_to_author": reply_to_author,
    }


def _notify_new_message(sender, receiver, message_preview):
    preview = (message_preview[:60] + '…') if len(message_preview) > 60 else message_preview
    msg_text = f"<strong>{sender.username}</strong> sent you a message: \"{preview}\""

    if receiver.role == 'applicant':
        existing = ApplicantNotification.query.filter_by(
            applicant_id=receiver.id,
            type='new_message',
            is_read=False,
            sender_id=sender.id
        ).first()
        if existing:
            existing.message = msg_text
            existing.created_at = get_ph_time()
            existing.is_read = False
        else:
            db.session.add(ApplicantNotification(
                applicant_id=receiver.id,
                type='new_message',
                message=msg_text,
                sender_id=sender.id
            ))

    elif receiver.role == 'recruiter':
        existing = RecruiterNotification.query.filter_by(
            recruiter_id=receiver.id,
            type='new_message',
            is_read=False,
            sender_id=sender.id
        ).first()
        if existing:
            existing.message = msg_text
            existing.created_at = get_ph_time()
            existing.is_read = False
        else:
            db.session.add(RecruiterNotification(
                recruiter_id=receiver.id,
                type='new_message',
                message=msg_text,
                sender_id=sender.id
            ))

    elif receiver.role == 'hr':
        existing = HRNotification.query.filter_by(
            hr_id=receiver.id,
            type='new_message',
            is_read=False,
            sender_id=sender.id
        ).first()
        if existing:
            existing.message = msg_text
            existing.created_at = get_ph_time()
            existing.is_read = False
        else:
            db.session.add(HRNotification(
                hr_id=receiver.id,
                type='new_message',
                message=msg_text,
                sender_id=sender.id
            ))

def _notify_new_follow(follower, followed):
    """
    Create a new_follow notification for the followed user regardless of role.
    """
    msg_text = f"<strong>{follower.username}</strong> started following you."

    if followed.role == 'applicant':
        notif = ApplicantNotification(
            applicant_id=followed.id,
            type='new_follow',
            message=msg_text,
            sender_id=follower.id,
        )
        db.session.add(notif)

    elif followed.role == 'recruiter':
        notif = RecruiterNotification(
            recruiter_id=followed.id,
            type='new_follow',
            message=msg_text,
            sender_id=follower.id,
        )
        db.session.add(notif)

    elif followed.role == 'hr':
        notif = HRNotification(
            hr_id=followed.id,
            type='new_follow',
            message=msg_text,
            sender_id=follower.id,
        )
        db.session.add(notif)

def _notify_follow_request(sender, receiver):
    """Notify the receiver that someone sent a follow request."""
    msg_text = f"<strong>{sender.username}</strong> sent you a follow request."

    if receiver.role == 'applicant':
        db.session.add(ApplicantNotification(
            applicant_id=receiver.id,
            type='follow_request',
            message=msg_text,
            sender_id=sender.id,
        ))
    elif receiver.role == 'recruiter':
        db.session.add(RecruiterNotification(
            recruiter_id=receiver.id,
            type='follow_request',
            message=msg_text,
            sender_id=sender.id,
        ))
    elif receiver.role == 'hr':
        db.session.add(HRNotification(
            hr_id=receiver.id,
            type='follow_request',
            message=msg_text,
            sender_id=sender.id,
        ))
    
# =========================
# PEOPLE PAGE
# =========================
@chat_bp.route("/people")
def people():
    query       = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()

    users_query = User.query.filter(User.role != "admin", User.is_banned == False)

    if current_user.is_authenticated:
        from models import UserBlock
        _blocked_out = db.session.query(UserBlock.blocked_id).filter_by(blocker_id=current_user.id)
        _blocked_in  = db.session.query(UserBlock.blocker_id).filter_by(blocked_id=current_user.id)
        users_query = users_query.filter(
            User.id.not_in(_blocked_out),
            User.id.not_in(_blocked_in),
        )

    if current_user.is_authenticated:
        users_query = users_query.filter(User.id != current_user.id)

    if query:
        users_query = users_query.filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )

    if role_filter in ["applicant", "recruiter", "hr"]:
        users_query = users_query.filter(User.role == role_filter)

    users_query = users_query.filter(
        or_(
            User.verification_status == "Approved",
            User.role == "applicant",
            User.role == "hr"
        )
    )

    users = users_query.order_by(User.username).all()

    # Pre-fetch all follow relationships for the current viewer in one query
    # to avoid N+1 queries inside build_user_card
    current_id   = current_user.id   if current_user.is_authenticated else None
    current_role = current_user.role if current_user.is_authenticated else None

    following_ids = set()
    if current_id:
        rows = Follow.query.filter_by(follower_id=current_id).all()
        following_ids = {r.followed_id for r in rows}

    user_cards = [
        build_user_card(u, current_id, current_role, following_ids)
        for u in users
    ]

    return render_template(
        "chat/people.html",
        user_cards=user_cards,
        query=query,
        role_filter=role_filter
    )


# =========================
# FOLLOW / UNFOLLOW  (AJAX)
# =========================
@chat_bp.route("/follow/<int:target_id>", methods=["POST"])
@login_required
def follow(target_id):
    from models import FollowRequest

    target = User.query.get_or_404(target_id)

    if target.id == current_user.id:
        return jsonify({"error": "Cannot follow yourself"}), 400

    # ── If already following, unfollow immediately ──
    existing = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        follower_count = Follow.query.filter_by(followed_id=target.id).count()
        return jsonify({"action": "unfollowed", "follower_count": follower_count})

    # ── Determine if approval is needed ──
    settings = get_user_settings(target.id)
    show_profile = settings["show_profile"]
    audience     = settings["profile_audience"]

    # Approval is needed ONLY when profile is 'specific' AND 'follower' is
    # in the audience list AND the current viewer is NOT already in a
    # privileged role that bypasses approval (recruiter/hr who are in audience).
    viewer_role = current_user.role
    viewer_in_privileged_audience = (
        (viewer_role == "recruiter" and "recruiter" in audience) or
        (viewer_role == "hr"        and "hr"        in audience)
    )

    requires_approval = (
        show_profile == "specific"
        and "follower" in audience
        and not viewer_in_privileged_audience
    )

    # If profile is public or viewer already has privileged access,
    # auto-accept any stale pending request then follow immediately.
    if not requires_approval:
        # Clean up any stale pending request
        stale = FollowRequest.query.filter_by(
            sender_id=current_user.id,
            receiver_id=target.id,
        ).first()
        if stale:
            db.session.delete(stale)

        new_follow = Follow(follower_id=current_user.id, followed_id=target.id)
        db.session.add(new_follow)
        _notify_new_follow(current_user, target)
        db.session.commit()

        follower_count = Follow.query.filter_by(followed_id=target.id).count()
        return jsonify({"action": "followed", "follower_count": follower_count})

    # ── Approval needed ──
    existing_req = FollowRequest.query.filter_by(
        sender_id=current_user.id,
        receiver_id=target.id
    ).first()

    if existing_req:
        if existing_req.status == 'pending':
            # Cancel the pending request
            db.session.delete(existing_req)
            db.session.commit()
            return jsonify({"action": "request_cancelled"})
        else:
            # Re-send a previously rejected request
            existing_req.status = 'pending'
            existing_req.created_at = get_ph_time()
            db.session.commit()
            _notify_follow_request(current_user, target)
            db.session.commit()
            return jsonify({"action": "request_sent"})

    # Create new follow request
    req = FollowRequest(sender_id=current_user.id, receiver_id=target.id)
    db.session.add(req)
    _notify_follow_request(current_user, target)
    db.session.commit()
    return jsonify({"action": "request_sent"})


# =========================
# INBOX — list all conversations
# =========================
@chat_bp.route("/inbox")
@login_required
def inbox():
    sent_to       = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)

    contact_ids = set(
        [r[0] for r in sent_to.all()] +
        [r[0] for r in received_from.all()]
    )

    conversations = []
    for uid in contact_ids:
        user = User.query.get(uid)
        if not user or user.is_banned:
            continue
        from models import UserBlock
        _blk = UserBlock.query.filter(
            or_(
                and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == uid),
                and_(UserBlock.blocker_id == uid,             UserBlock.blocked_id == current_user.id),
            )
        ).first()
        if _blk:
            continue

        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == uid),
                and_(Message.sender_id == uid, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.desc()).first()

        unread_count = Message.query.filter_by(
            sender_id=uid, receiver_id=current_user.id, is_read=False
        ).count()

        conversations.append({
            "user":         user,
            "display_name": get_display_name(user),
            "company":      get_company_name(user),
            "last_message": last_msg,
            "unread_count": unread_count,
        })

    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else datetime.min,
        reverse=True
    )

    total_unread = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()

    # Redirect to most recent conversation if one exists
    if conversations:
        most_recent_id = conversations[0]["user"].id
        return redirect(url_for("chat.conversation", other_id=most_recent_id))

    return render_template(
        "chat/inbox.html",
        conversations=conversations,
        active_user=None,
        messages=[],
        total_unread=total_unread
    )


@chat_bp.route("/inbox/<int:other_id>")
@login_required
def conversation(other_id):
    other = User.query.get_or_404(other_id)

    if other.is_banned:
        flash("This user is not available.", "warning")
        return redirect(url_for('chat.inbox'))

    # Build sidebar FIRST — captures unread counts before marking read
    sent_to       = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    contact_ids   = set(
        [r[0] for r in sent_to.all()] +
        [r[0] for r in received_from.all()]
    )
    contact_ids.add(other_id)

    from models import UserBlock

    conversations = []
    for uid in contact_ids:
        u = User.query.get(uid)
        if not u or u.is_banned:
            continue

        _blk = UserBlock.query.filter(
            or_(
                and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == uid),
                and_(UserBlock.blocker_id == uid,             UserBlock.blocked_id == current_user.id),
            )
        ).first()
        if _blk:
            continue

        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == uid),
                and_(Message.sender_id == uid, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.desc()).first()

        # Count unread BEFORE marking as read so badge shows correctly
        unread_count = Message.query.filter_by(
            sender_id=uid, receiver_id=current_user.id, is_read=False
        ).count()

        conversations.append({
            "user":         u,
            "display_name": get_display_name(u),
            "company":      get_company_name(u),
            "last_message": last_msg,
            "unread_count": unread_count,
        })

    conversations.sort(
        key=lambda c: c["last_message"].created_at if c["last_message"] else datetime.min,
        reverse=True
    )

    # Mark incoming messages as read AFTER sidebar is built
    Message.query.filter_by(
        sender_id=other_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({"is_read": True})
    db.session.commit()

    # Active conversation messages
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    messages = [m for m in messages if not (m.hidden_for and str(current_user.id) in m.hidden_for.split(','))]

    total_unread = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()

    is_following = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=other_id
    ).first() is not None

    msg_ids = [m.id for m in messages]
    all_rxns = MessageReaction.query.filter(
        MessageReaction.message_id.in_(msg_ids)
    ).all() if msg_ids else []

    reaction_map = {}
    for r in all_rxns:
        entry = reaction_map.setdefault(r.message_id, {"counts": {}, "my_reaction": ""})
        entry["counts"][r.reaction] = entry["counts"].get(r.reaction, 0) + 1
        if r.user_id == current_user.id:
            entry["my_reaction"] = r.reaction

    return render_template(
        "chat/inbox.html",
        conversations=conversations,
        active_user=other,
        active_display_name=get_display_name(other),
        active_company=get_company_name(other),
        messages=messages,
        reaction_map=reaction_map,
        total_unread=total_unread,
        is_following=is_following,
    )

# =========================
# SEND MESSAGE  (AJAX POST)
# =========================
@chat_bp.route("/send/<int:receiver_id>", methods=["POST"])
@login_required
def send_message(receiver_id):
    receiver = User.query.get_or_404(receiver_id)

    if receiver.is_banned:
        return jsonify({'error': 'You cannot message this user.'}), 403

    from models import UserBlock
    
    _block = UserBlock.query.filter(
        or_(
            and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == receiver.id),
            and_(UserBlock.blocker_id == receiver.id,     UserBlock.blocked_id == current_user.id),
        )
    ).first()
    if _block:
        return jsonify({'error': 'You cannot message this user.'}), 403

    data     = request.get_json()
    body     = (data.get("body") or "").strip()

    if not body:
        return jsonify({"error": "Empty message"}), 400

    if len(body) > 2000:
        return jsonify({"error": "Message too long"}), 400

    # ── reply support ──
    reply_to_id = data.get("reply_to_id")
    if reply_to_id:
        quoted = Message.query.get(reply_to_id)
        if not quoted or not (
            (quoted.sender_id == current_user.id   and quoted.receiver_id == receiver_id) or
            (quoted.sender_id == receiver_id        and quoted.receiver_id == current_user.id)
        ):
            reply_to_id = None

    msg = Message(
        sender_id   = current_user.id,
        receiver_id = receiver.id,
        body        = body,
        reply_to_id = reply_to_id,
    )
    db.session.add(msg)

    # Notify receiver of new message (for all roles)
    try:
        _notify_new_message(current_user, receiver, body)
    except Exception as e:
        print(f"[NOTIF ERROR] {e}")

    db.session.commit()

    # Build reply preview fields for the JS
    reply_to_body   = None
    reply_to_author = None
    if reply_to_id and msg.reply_to:
        reply_to_body   = msg.reply_to.body
        reply_to_author = "You" if msg.reply_to.sender_id == current_user.id else get_display_name(receiver)

    return jsonify({
        "id":              msg.id,
        "body":            msg.body,
        "sender_id":       msg.sender_id,
        "created_at":      msg.created_at.strftime("%I:%M %p"),
        "is_mine":         True,
        "edited":          False,
        "reply_to_id":     msg.reply_to_id,
        "reply_to_body":   reply_to_body,
        "reply_to_author": reply_to_author,
    })


# =========================
# POLL FOR NEW MESSAGES  (AJAX GET)
# =========================
@chat_bp.route("/poll/<int:other_id>")
@login_required
def poll_messages(other_id):
    since_id = request.args.get("since", 0, type=int)

    other = User.query.get_or_404(other_id)

    new_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id,        Message.receiver_id == current_user.id)
        ),
        Message.id > since_id
    ).order_by(Message.created_at.asc()).all()

    new_messages = [m for m in new_messages if not (m.hidden_for and str(current_user.id) in m.hidden_for.split(','))]

    # Mark incoming as read
    for m in new_messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()

    other_display = get_display_name(other)

    # Edited messages the client already knows about (id <= since_id)
    edited_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id,        Message.receiver_id == current_user.id)
        ),
        Message.edited == True,
        Message.id <= since_id
    ).all() if since_id > 0 else []

    # Deleted / hidden: client sends comma-separated known_ids; we return which are gone or hidden for current user
    known_ids_param = request.args.get("known_ids", "")
    client_known = set(int(i) for i in known_ids_param.split(",") if i.strip().isdigit())
    deleted_ids = []
    if client_known:
        existing_msgs = Message.query.filter(
            Message.id.in_(client_known)
        ).all()
        existing_map = {m.id: m for m in existing_msgs}
        for kid in client_known:
            msg_obj = existing_map.get(kid)
            if msg_obj is None:
                deleted_ids.append(kid)
            elif msg_obj.hidden_for and str(current_user.id) in msg_obj.hidden_for.split(','):
                deleted_ids.append(kid)

    return jsonify({
        "messages": [serialize_message(m, current_user.id, other_display) for m in new_messages],
        "edited":   [{"id": m.id, "body": m.body} for m in edited_messages],
        "deleted":  deleted_ids,
    })


# =========================
# POLL REACTIONS  (AJAX GET)
# =========================
@chat_bp.route("/poll-reactions/<int:other_id>")
@login_required
def poll_reactions(other_id):
    """
    Return current reaction counts + my_reaction for every message
    in the conversation. Called periodically by the frontend so reactions
    update in real-time without a full page refresh.
    """
    msg_ids_query = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_id),
            and_(Message.sender_id == other_id,        Message.receiver_id == current_user.id)
        )
    ).with_entities(Message.id)

    msg_ids = [row.id for row in msg_ids_query.all()]
    if not msg_ids:
        return jsonify({})

    all_rxns = MessageReaction.query.filter(
        MessageReaction.message_id.in_(msg_ids)
    ).all()

    # Build { "msg_id": { "counts": { "like": 2, ... }, "my_reaction": "like" } }
    result = {}
    for r in all_rxns:
        mid = str(r.message_id)
        if mid not in result:
            result[mid] = {"counts": {}, "my_reaction": ""}
        result[mid]["counts"][r.reaction] = result[mid]["counts"].get(r.reaction, 0) + 1
        if r.user_id == current_user.id:
            result[mid]["my_reaction"] = r.reaction

    # Include messages that now have zero reactions so JS can clear their bars
    for mid in msg_ids:
        if str(mid) not in result:
            result[str(mid)] = {"counts": {}, "my_reaction": ""}

    return jsonify(result)


# =========================
# UNREAD COUNT  (AJAX — for nav badge)
# =========================
@chat_bp.route("/unread-count")
@login_required
def unread_count():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({"count": count})


# =========================
# EDIT MESSAGE  (AJAX POST)
# =========================
@chat_bp.route("/edit/<int:msg_id>", methods=["POST"])
@login_required
def edit_message(msg_id):
    msg = Message.query.get_or_404(msg_id)

    if msg.sender_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data     = request.get_json()
    new_body = (data.get("body") or "").strip()

    if not new_body:
        return jsonify({"error": "Empty message"}), 400

    if len(new_body) > 2000:
        return jsonify({"error": "Message too long"}), 400

    msg.body   = new_body
    msg.edited = True
    db.session.commit()

    return jsonify({
        "id":     msg.id,
        "body":   msg.body,
        "edited": True,
    })


# =========================
# UNSEND MESSAGE  (AJAX POST)
# =========================
@chat_bp.route("/unsend/<int:msg_id>", methods=["POST"])
@login_required
def unsend_message(msg_id):
    msg = Message.query.get_or_404(msg_id)

    if msg.sender_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    Message.query.filter_by(reply_to_id=msg_id).update({"reply_to_id": None})

    db.session.delete(msg)
    db.session.commit()

    return jsonify({"deleted": True, "id": msg_id})

@chat_bp.route("/remove-for-me/<int:msg_id>", methods=["POST"])
@login_required
def remove_for_me(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if not (msg.sender_id == current_user.id or msg.receiver_id == current_user.id):
        return jsonify({"error": "Unauthorized"}), 403

    # Store which users have hidden this message
    if not msg.hidden_for:
        msg.hidden_for = str(current_user.id)
    else:
        ids = msg.hidden_for.split(',')
        if str(current_user.id) not in ids:
            ids.append(str(current_user.id))
            msg.hidden_for = ','.join(ids)
    db.session.commit()
    return jsonify({"deleted": True, "id": msg_id})

# =========================
# REACT MESSAGE  (AJAX POST)
# =========================
VALID_REACTIONS = {"like", "heart", "haha", "wow", "sad", "angry"}

@chat_bp.route("/react/<int:msg_id>", methods=["POST"])
@login_required
def react_message(msg_id):
    msg = Message.query.get_or_404(msg_id)

    # Verify the message belongs to the current conversation
    if not (
        (msg.sender_id == current_user.id) or
        (msg.receiver_id == current_user.id)
    ):
        return jsonify({"error": "Unauthorized"}), 403

    data     = request.get_json()
    reaction = (data.get("reaction") or "").strip().lower()

    if reaction not in VALID_REACTIONS:
        return jsonify({"error": "Invalid reaction"}), 400

    existing = MessageReaction.query.filter_by(
        message_id=msg_id, user_id=current_user.id
    ).first()

    if existing:
        if existing.reaction == reaction:
            # Toggle off — remove reaction
            db.session.delete(existing)
            db.session.commit()
            action = "removed"
        else:
            # Change reaction
            existing.reaction = reaction
            db.session.commit()
            action = "changed"
    else:
        new_r = MessageReaction(
            message_id=msg_id,
            user_id=current_user.id,
            reaction=reaction
        )
        db.session.add(new_r)
        db.session.commit()
        action = "added"

    # Return aggregated counts for this message
    all_reactions = MessageReaction.query.filter_by(message_id=msg_id).all()
    counts = {}
    for r in all_reactions:
        counts[r.reaction] = counts.get(r.reaction, 0) + 1

    my_reaction = None
    my = MessageReaction.query.filter_by(
        message_id=msg_id, user_id=current_user.id
    ).first()
    if my:
        my_reaction = my.reaction

    return jsonify({
        "action":      action,
        "msg_id":      msg_id,
        "counts":      counts,
        "my_reaction": my_reaction,
    })