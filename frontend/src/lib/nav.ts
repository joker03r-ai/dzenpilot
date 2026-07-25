import {
  BarChart3,
  CalendarDays,
  FileText,
  LayoutDashboard,
  Lightbulb,
  Plug,
  Settings,
  Users,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
  /** Раздел появится на следующем этапе разработки */
  stage?: number;
}

export const NAV_ITEMS: NavItem[] = [
  {
    href: '/dashboard',
    label: 'Главная',
    description: 'Общая картина и подсказки, что делать дальше',
    icon: LayoutDashboard,
  },
  {
    href: '/competitors',
    label: 'Конкуренты',
    description: 'Каналы вашей тематики и разбор их публикаций',
    icon: Users,
  },
  {
    href: '/topics',
    label: 'Поиск тем',
    description: 'Перспективные темы с оценкой от 0 до 100',
    icon: Lightbulb,
  },
  {
    href: '/articles',
    label: 'Статьи',
    description: 'Библиотека статей и мастер создания',
    icon: FileText,
  },
  {
    href: '/calendar',
    label: 'Контент-календарь',
    description: 'План публикаций по датам и часовым поясам',
    icon: CalendarDays,
  },
  {
    href: '/analytics',
    label: 'Аналитика',
    description: 'Просмотры, подписчики и сравнение с конкурентами',
    icon: BarChart3,
  },
  {
    href: '/integrations',
    label: 'Интеграции',
    description: 'Подключение моделей ИИ, канала и уведомлений',
    icon: Plug,
  },
  {
    href: '/settings',
    label: 'Настройки',
    description: 'Профиль, проект, модель ИИ и безопасность',
    icon: Settings,
  },
];
