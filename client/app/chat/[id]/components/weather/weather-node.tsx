import { AgentState } from "../../agent-types";
import { Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import Rain from "./rain";
import Clear from "./clear";
import Clouds from "./clouds";
import Snow from "./snow";

interface WeatherNodeProps {
  nodeState: Partial<AgentState>;
}

export default function WeatherNode({ nodeState }: WeatherNodeProps) {
  if (nodeState?.weather_forecast?.[0]?.search_status) {
    return (
      <div className="flex justify-end">
        <Card className="inline-block">
          <CardContent className="p-2">
            <div className="flex items-center gap-2">
              <Loader2 className="w-6 h-6 animate-spin" />
              <div className="text-sm">{nodeState?.weather_forecast?.[0]?.search_status}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!nodeState?.weather_forecast?.[0]?.result) {
    return null;
  }

  const WeatherComponents = {
    Clear,
    Clouds,
    Rain,
    Snow,
  } as const;

  const WeatherComponent = WeatherComponents[nodeState?.weather_forecast?.[0].result];

  return (
    <div className="flex justify-end">
      <WeatherComponent />
    </div>
  );
}