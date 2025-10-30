# shiftapp/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from shiftapp.models import Members, LeaveBalance

VALID_POSITIONS = ['full', 'part']

@receiver(pre_save, sender=Members)
def check_position_change(sender, instance, **kwargs):
    """
    在更新 Members 前，記錄舊的 position_type，
    以便 post_save 判斷是否從 casual → full/part。
    """
    if not instance.pk:  # 新建時沒有舊資料，略過
        return
    try:
        old_instance = Members.objects.get(pk=instance.pk)
        instance._old_position_type = old_instance.position_type
    except Members.DoesNotExist:
        instance._old_position_type = None


@receiver(post_save, sender=Members)
def create_or_update_leave_balance(sender, instance, created, **kwargs):
    """
    1. 新增時：若是 full/part 則建立 LeaveBalance。
    2. 更新時：若職位從 casual → full/part，也建立 LeaveBalance。
    """
    if created:
        if instance.position_type in VALID_POSITIONS:
            LeaveBalance.objects.get_or_create(staff=instance)
            print(f"[Signal] Created LeaveBalance for {instance.email}")
        return
    
    # --- 更新情境 ---
    old_position = getattr(instance, "_old_position_type", None)
    new_position = instance.position_type

    # casual → full/part
    if old_position not in VALID_POSITIONS and new_position in VALID_POSITIONS:
        LeaveBalance.objects.get_or_create(staff=instance)
        print(f"[Signal] Added LeaveBalance for {instance.email} (converted from {old_position})")

    # full/part → casual（若你要刪除紀錄，也可以這裡處理）
    elif old_position in VALID_POSITIONS and new_position not in VALID_POSITIONS:
        LeaveBalance.objects.filter(staff=instance).delete()
        print(f"[Signal] Removed LeaveBalance for {instance.email} (converted to {new_position})")

    elif not instance.is_active:
        LeaveBalance.objects.filter(staff=instance).delete()
        print(f"[Signal] Removed LeaveBalance for {instance.email} (converted to inactive)")
