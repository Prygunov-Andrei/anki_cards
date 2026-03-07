import React from 'react';
import { useTranslation } from '../contexts/LanguageContext';
import { useAuthContext } from '../contexts/AuthContext';
import { formatTokensWithText } from '../utils/token-formatting';

interface TokenCostBadgeProps {
  cost: number;
  balance: number;
}

export const TokenCostBadge: React.FC<TokenCostBadgeProps> = ({
  cost,
  balance,
}) => {
  const t = useTranslation();
  const { user } = useAuthContext();
  const nativeLang = user?.native_language || 'en';
  const sufficient = balance >= cost;

  if (cost <= 0) return null;

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium
        ${sufficient
          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
        }
      `}
    >
      ~{formatTokensWithText(cost, t, nativeLang)}
    </span>
  );
};
