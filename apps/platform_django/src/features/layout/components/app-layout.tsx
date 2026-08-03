import { Home, LogOut, Moon, Sun, User } from 'lucide-react';
import { Link, Outlet } from 'react-router';

import { Button } from '@workspace/ui/components/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@workspace/ui/components/dropdown-menu';

import { useTheme } from '@/components/theme-provider';
import { useAuth } from '@/features/auth';

// Project identity is data: the template is never renamed, so the name a user
// reads comes from the environment rather than from this file. The fallback
// matches project_display_name() in config/env.py, so a clone that set only the
// slug reads the same here as it does server-side.
const projectDisplayName =
  import.meta.env.PROJECT_DISPLAY_NAME ||
  (import.meta.env.PROJECT_SLUG || 'app')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (character: string) => character.toUpperCase());

export function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <Link to="/" className="flex items-center space-x-2">
              <span className="font-bold">{projectDisplayName}</span>
            </Link>
          </div>
          <nav className="flex flex-1 items-center space-x-4 text-sm font-medium">
            <Link
              to="/"
              className="flex items-center text-muted-foreground transition-colors hover:text-foreground"
            >
              <Home className="mr-2 h-4 w-4" />
              Dashboard
            </Link>
          </nav>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              <Sun className="h-4 w-4 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
              <Moon className="absolute h-4 w-4 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
              <span className="sr-only">Toggle theme</span>
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <User className="h-4 w-4" />
                  <span className="sr-only">User menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <div className="flex items-center justify-start gap-2 p-2">
                  <div className="flex flex-col space-y-1 leading-none">
                    {user?.email && <p className="font-medium">{user.email}</p>}
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-6">
        <Outlet />
      </main>
    </div>
  );
}
