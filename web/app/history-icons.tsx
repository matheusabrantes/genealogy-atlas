import {
  Castle,
  Cross,
  Eye,
  Flag,
  Landmark,
  Scale,
  Shield,
  Swords,
} from "lucide-react";

const icons = {
  "inquisition-agents": Eye,
  inquisition: Scale,
  templars: Shield,
  "order-christ": Cross,
  "order-avis": Shield,
  "order-santiago": Cross,
  "order-hospital": Cross,
  crusades: Flag,
  reconquista: Castle,
  aljubarrota: Swords,
  "hundred-years-war": Swords,
  "norman-conquest": Landmark,
  "dutch-brazil": Swords,
};

export function HistoryIcon({
  context,
  size = 20,
}: {
  context: string;
  size?: number;
}) {
  const Icon = icons[context as keyof typeof icons] ?? Landmark;
  return <Icon aria-hidden="true" size={size} strokeWidth={1.8} />;
}
