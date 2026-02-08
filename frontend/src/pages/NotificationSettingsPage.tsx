import { useEffect, useState } from 'react';
import { Bell, BellOff, Clock, Shield, Zap, Volume2 } from 'lucide-react';
import { notificationsService } from '@/services/notifications.service';
import type { NotificationSettings, NotificationFrequency } from '@/types';
import { toast } from 'sonner';
import { useLanguage } from '@/contexts/LanguageContext';

export default function NotificationSettingsPage() {
  const { t } = useLanguage();
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    let cancelled = false;
    async function initialLoad() {
      try {
        const data = await notificationsService.getSettings();
        if (!cancelled) setSettings(data);
      } catch {
        if (!cancelled) toast.error(t.notificationSettings.errors.loadFailed);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    initialLoad();
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
    return () => { cancelled = true; };
  }, []);

  async function loadSettings() {
    try {
      const data = await notificationsService.getSettings();
      setSettings(data);
    } catch {
      toast.error(t.notificationSettings.errors.loadFailed);
    } finally {
      setLoading(false);
    }
  }

  async function updateField<K extends keyof NotificationSettings>(
    field: K,
    value: NotificationSettings[K],
  ) {
    if (!settings) return;
    const updated = { ...settings, [field]: value };
    setSettings(updated);

    setSaving(true);
    try {
      await notificationsService.updateSettings({ [field]: value });
    } catch {
      toast.error(t.notificationSettings.errors.saveFailed);
      loadSettings();
    } finally {
      setSaving(false);
    }
  }

  async function requestPermission() {
    const result = await notificationsService.requestPermission();
    setPermission(result);
    if (result === 'granted') {
      toast.success(t.notificationSettings.success.permissionGranted);
    } else if (result === 'denied') {
      toast.error(t.notificationSettings.errors.notificationsBlocked);
    }
  }

  async function sendTestNotification() {
    notificationsService.showBrowserNotification(
      t.notificationSettings.testNotification.title,
      t.notificationSettings.testNotification.message,
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!settings) return null;

  const frequencyOptions: { value: NotificationFrequency; label: string; desc: string }[] = [
    { value: 'aggressive', label: t.notificationSettings.frequency.aggressive.label, desc: t.notificationSettings.frequency.aggressive.desc },
    { value: 'normal', label: t.notificationSettings.frequency.normal.label, desc: t.notificationSettings.frequency.normal.desc },
    { value: 'minimal', label: t.notificationSettings.frequency.minimal.label, desc: t.notificationSettings.frequency.minimal.desc },
    { value: 'off', label: t.notificationSettings.frequency.off.label, desc: t.notificationSettings.frequency.off.desc },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Bell className="h-7 w-7 text-blue-600" />
        <h1 className="text-2xl font-bold">{t.notificationSettings.title}</h1>
      </div>

      {/* Browser Permission */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border p-5 space-y-4">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <Shield className="h-5 w-5" />
          {t.notificationSettings.browserPermission.title}
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {permission === 'granted'
                ? t.notificationSettings.browserPermission.granted
                : permission === 'denied'
                  ? t.notificationSettings.browserPermission.denied
                  : t.notificationSettings.browserPermission.notRequested}
            </p>
          </div>
          <div className="flex gap-2">
            {permission !== 'granted' && (
              <button
                onClick={requestPermission}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                {t.notificationSettings.browserPermission.allowButton}
              </button>
            )}
            {permission === 'granted' && (
              <button
                onClick={sendTestNotification}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 text-sm"
              >
                {t.notificationSettings.browserPermission.testButton}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Toggle */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {settings.browser_notifications_enabled ? (
              <Bell className="h-5 w-5 text-blue-600" />
            ) : (
              <BellOff className="h-5 w-5 text-gray-400" />
            )}
            <span className="font-semibold">{t.notificationSettings.mainToggle.label}</span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.browser_notifications_enabled}
              onChange={(e) => updateField('browser_notifications_enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all" />
          </label>
        </div>
      </div>

      {settings.browser_notifications_enabled && (
        <>
          {/* Frequency */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border p-5 space-y-4">
            <div className="flex items-center gap-2 font-semibold">
              <Zap className="h-5 w-5" />
              {t.notificationSettings.frequency.title}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {frequencyOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => updateField('notification_frequency', opt.value)}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    settings.notification_frequency === opt.value
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-sm">{opt.label}</div>
                  <div className="text-xs text-gray-500">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Triggers */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border p-5 space-y-4">
            <div className="flex items-center gap-2 font-semibold">
              <Volume2 className="h-5 w-5" />
              {t.notificationSettings.triggers.title}
            </div>
            {[
              { key: 'notify_cards_due' as const, label: t.notificationSettings.triggers.cardsDue.label, desc: t.notificationSettings.triggers.cardsDue.desc },
              { key: 'notify_streak_warning' as const, label: t.notificationSettings.triggers.streakWarning.label, desc: t.notificationSettings.triggers.streakWarning.desc },
              { key: 'notify_daily_goal' as const, label: t.notificationSettings.triggers.dailyGoal.label, desc: t.notificationSettings.triggers.dailyGoal.desc },
            ].map((trigger) => (
              <div key={trigger.key} className="flex items-center justify-between py-2">
                <div>
                  <div className="text-sm font-medium">{trigger.label}</div>
                  <div className="text-xs text-gray-500">{trigger.desc}</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings[trigger.key]}
                    onChange={(e) => updateField(trigger.key, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all" />
                </label>
              </div>
            ))}
            <div className="pt-2 border-t">
              <label className="text-sm font-medium block mb-2">
                {t.notificationSettings.triggers.cardsThreshold}
              </label>
              <input
                type="number"
                min={1}
                max={500}
                value={settings.cards_due_threshold}
                onChange={(e) => updateField('cards_due_threshold', parseInt(e.target.value) || 5)}
                className="w-24 px-3 py-2 border rounded-lg text-sm dark:bg-gray-700"
              />
            </div>
          </div>

          {/* Quiet Hours */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border p-5 space-y-4">
            <div className="flex items-center gap-2 font-semibold">
              <Clock className="h-5 w-5" />
              {t.notificationSettings.quietHours.title}
            </div>
            <p className="text-sm text-gray-500">
              {t.notificationSettings.quietHours.description}
            </p>
            <div className="flex items-center gap-4">
              <div>
                <label className="text-xs text-gray-500 block mb-1">{t.notificationSettings.quietHours.from}</label>
                <input
                  type="time"
                  value={settings.quiet_hours_start}
                  onChange={(e) => updateField('quiet_hours_start', e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm dark:bg-gray-700"
                />
              </div>
              <span className="text-gray-400 mt-5">—</span>
              <div>
                <label className="text-xs text-gray-500 block mb-1">{t.notificationSettings.quietHours.to}</label>
                <input
                  type="time"
                  value={settings.quiet_hours_end}
                  onChange={(e) => updateField('quiet_hours_end', e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm dark:bg-gray-700"
                />
              </div>
            </div>
          </div>
        </>
      )}

      {saving && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm animate-pulse">
          {t.notificationSettings.saving}
        </div>
      )}
    </div>
  );
}
