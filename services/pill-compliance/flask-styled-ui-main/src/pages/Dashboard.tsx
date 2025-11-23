import { Card } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, Clock, TrendingUp, Activity, History as HistoryIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const navigate = useNavigate();

  const stats = [
    { label: "Adherence Rate", value: "94%", icon: TrendingUp, color: "text-success" },
    { label: "Successful Sessions", value: "23", icon: CheckCircle2, color: "text-success" },
    { label: "Pending Doses", value: "2", icon: Clock, color: "text-warning" },
    { label: "Alerts", value: "0", icon: AlertCircle, color: "text-muted-foreground" },
  ];

  const recentSessions = [
    { date: "2024-01-15", time: "08:30 AM", status: "PASS", phase: "Completed" },
    { date: "2024-01-15", time: "02:00 PM", status: "PASS", phase: "Completed" },
    { date: "2024-01-14", time: "08:30 AM", status: "PASS", phase: "Completed" },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back!</h1>
        <p className="text-muted-foreground">Monitor your medication adherence protocol</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <Card key={index} className="p-6 shadow-card hover:shadow-elevated transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <stat.icon className={`w-8 h-8 ${stat.color}`} />
            </div>
            <div className="text-3xl font-bold text-foreground mb-1">{stat.value}</div>
            <div className="text-sm text-muted-foreground">{stat.label}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 shadow-card">
          <h2 className="text-xl font-semibold text-foreground mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Button 
              className="w-full justify-start" 
              variant="default"
              onClick={() => navigate("/monitor")}
            >
              <Activity className="w-4 h-4 mr-2" />
              Start New Session
            </Button>
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={() => navigate("/history")}
            >
              <HistoryIcon className="w-4 h-4 mr-2" />
              View Session History
            </Button>
          </div>
        </Card>

        <Card className="p-6 shadow-card">
          <h2 className="text-xl font-semibold text-foreground mb-4">Recent Sessions</h2>
          <div className="space-y-3">
            {recentSessions.map((session, index) => (
              <div 
                key={index} 
                className="flex items-center justify-between p-3 rounded-lg bg-accent/50 hover:bg-accent transition-colors"
              >
                <div>
                  <div className="text-sm font-medium text-foreground">{session.date}</div>
                  <div className="text-xs text-muted-foreground">{session.time}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">{session.phase}</div>
                  <div className="text-sm font-semibold text-success">{session.status}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
