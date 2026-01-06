'use client'

import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { 
  LayoutDashboard, 
  MessageSquare, 
  Library, 
  Database,
  Calendar,
  ListChecks,
  Newspaper,
  History,
  Settings,
  Upload,
  Users,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Brain
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth'
import { useState } from 'react'

interface SidebarProps {
  className?: string
}

const mainNavItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/library', label: 'Library', icon: Library },
  { href: '/databank', label: 'Data Bank', icon: Database },
]

const toolsNavItems = [
  { href: '/meeting-prep', label: 'Meeting Prep', icon: Calendar },
  { href: '/talking-points', label: 'Talking Points', icon: ListChecks },
  { href: '/news', label: 'News Analysis', icon: Newspaper },
]

const adminNavItems = [
  { href: '/admin', label: 'Admin Dashboard', icon: Settings },
  { href: '/admin/upload', label: 'Bulk Upload', icon: Upload },
  { href: '/admin/users', label: 'Users', icon: Users },
]

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, signOut } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)
  
  const isAdmin = user?.user_metadata?.is_admin || user?.email === 's.falasi@gmail.com'

  const handleLogout = async () => {
    await signOut()
    router.push('/login')
  }

  const NavItem = ({ href, label, icon: Icon }: { href: string; label: string; icon: any }) => {
    const isActive = pathname === href || pathname.startsWith(href + '/')
    
    return (
      <Link
        href={href}
        className={cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
          isActive 
            ? 'bg-primary text-primary-foreground' 
            : 'text-muted-foreground hover:bg-accent hover:text-foreground',
          collapsed && 'justify-center px-2'
        )}
        title={collapsed ? label : undefined}
      >
        <Icon className="h-5 w-5 flex-shrink-0" />
        {!collapsed && <span>{label}</span>}
      </Link>
    )
  }

  return (
    <aside className={cn(
      'flex flex-col h-screen border-r bg-card transition-all duration-300',
      collapsed ? 'w-16' : 'w-64',
      className
    )}>
      {/* Header */}
      <div className={cn(
        'flex items-center h-16 px-4 border-b',
        collapsed ? 'justify-center' : 'justify-between'
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" />
            <span className="font-semibold">DCAI Intel</span>
          </div>
        )}
        {collapsed && <Brain className="h-6 w-6 text-primary" />}
        <Button
          variant="ghost"
          size="icon"
          className={cn('h-8 w-8', collapsed && 'absolute -right-3 bg-background border shadow-sm')}
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-6">
        {/* Main */}
        <div className="space-y-1">
          {!collapsed && (
            <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Main
            </p>
          )}
          {mainNavItems.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </div>

        {/* Tools */}
        <div className="space-y-1">
          {!collapsed && (
            <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Tools
            </p>
          )}
          {toolsNavItems.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </div>

        {/* History */}
        <div className="space-y-1">
          {!collapsed && (
            <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              History
            </p>
          )}
          <NavItem href="/history" label="Conversations" icon={History} />
        </div>

        {/* Admin */}
        {isAdmin && (
          <div className="space-y-1">
            {!collapsed && (
              <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                Admin
              </p>
            )}
            {adminNavItems.map((item) => (
              <NavItem key={item.href} {...item} />
            ))}
          </div>
        )}
      </nav>

      {/* User */}
      <div className="border-t p-3">
        <div className={cn(
          'flex items-center gap-3',
          collapsed && 'justify-center'
        )}>
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-medium">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.email}</p>
              <p className="text-xs text-muted-foreground">
                {isAdmin ? 'Admin' : 'User'}
              </p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 flex-shrink-0"
            onClick={handleLogout}
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  )
}
