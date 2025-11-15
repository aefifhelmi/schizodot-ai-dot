import { NavLink } from "@/components/NavLink";
import { Activity, LayoutDashboard, History, Settings } from "lucide-react";

const Navigation = () => {
  const navItems = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/monitor", icon: Activity, label: "Monitor" },
    { to: "/history", icon: History, label: "History" },
    { to: "/settings", icon: Settings, label: "Settings" },
  ];

  return (
    <nav className="bg-card border-b border-border shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">💊</span>
            </div>
            <span className="font-bold text-xl text-foreground">MedAdhere</span>
          </div>
          
          <div className="hidden md:flex space-x-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors text-muted-foreground hover:text-foreground hover:bg-accent"
                activeClassName="bg-accent text-accent-foreground font-medium"
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="md:hidden flex space-x-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className="p-2 rounded-lg transition-colors text-muted-foreground hover:text-foreground hover:bg-accent"
                activeClassName="bg-accent text-accent-foreground"
              >
                <item.icon className="w-5 h-5" />
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
