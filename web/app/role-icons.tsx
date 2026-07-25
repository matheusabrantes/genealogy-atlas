import {
  Church,
  Compass,
  Crown,
  Hammer,
  Landmark,
  Scale,
  Shield,
  Stethoscope,
  Wheat,
} from "lucide-react";

const icons = {
  "royalty-nobility": Crown,
  "military-orders": Shield,
  government: Landmark,
  church: Church,
  "justice-inquisition": Scale,
  trades: Hammer,
  "land-agriculture": Wheat,
  navigation: Compass,
  "knowledge-medicine": Stethoscope,
};

export function RoleIcon({
  category,
  size = 18,
}: {
  category: string;
  size?: number;
}) {
  const Icon = icons[category as keyof typeof icons] ?? Landmark;
  return <Icon size={size} aria-hidden="true" />;
}
