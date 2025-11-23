import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Calendar, Clock } from "lucide-react";

const History = () => {
  const sessions = [
    { id: 1, date: "2024-01-15", time: "08:30 AM", status: "PASS", duration: "45s", phases: 6 },
    { id: 2, date: "2024-01-15", time: "02:00 PM", status: "PASS", duration: "38s", phases: 6 },
    { id: 3, date: "2024-01-14", time: "08:30 AM", status: "PASS", duration: "42s", phases: 6 },
    { id: 4, date: "2024-01-14", time: "02:00 PM", status: "PASS", duration: "51s", phases: 6 },
    { id: 5, date: "2024-01-13", time: "08:30 AM", status: "FAIL", duration: "23s", phases: 3 },
    { id: 6, date: "2024-01-13", time: "02:00 PM", status: "PASS", duration: "44s", phases: 6 },
    { id: 7, date: "2024-01-12", time: "08:30 AM", status: "PASS", duration: "39s", phases: 6 },
    { id: 8, date: "2024-01-12", time: "02:00 PM", status: "PASS", duration: "46s", phases: 6 },
  ];

  const getStatusBadge = (status: string) => {
    if (status === "PASS") {
      return (
        <Badge className="bg-success text-success-foreground">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          {status}
        </Badge>
      );
    }
    return (
      <Badge variant="destructive">
        <XCircle className="w-3 h-3 mr-1" />
        {status}
      </Badge>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Session History</h1>
        <p className="text-muted-foreground">Review your medication adherence protocol sessions</p>
      </div>

      <div className="grid gap-4">
        {sessions.map((session) => (
          <Card key={session.id} className="p-6 shadow-card hover:shadow-elevated transition-shadow">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <span className="text-2xl">💊</span>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Session #{session.id}</h3>
                  <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {session.date}
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {session.time}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm text-muted-foreground mb-1">Duration</div>
                  <div className="font-semibold text-foreground">{session.duration}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground mb-1">Phases</div>
                  <div className="font-semibold text-foreground">{session.phases}/6</div>
                </div>
                {getStatusBadge(session.status)}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default History;
