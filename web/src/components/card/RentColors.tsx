import { Flex } from "@/components/ui/flex";

import { COLOR_MAP } from "./colors";

interface RentColorsProps {
  colors: string[];
}

export function RentColors({ colors }: RentColorsProps) {
  return (
    <Flex
      className="h-[0.92rem] w-[5.6rem] overflow-hidden border border-[#222936]"
      gap="none"
    >
      {colors.map((color) => (
        <span
          key={color}
          className="flex-1"
          style={{ backgroundColor: COLOR_MAP[color] }}
        />
      ))}
    </Flex>
  );
}
