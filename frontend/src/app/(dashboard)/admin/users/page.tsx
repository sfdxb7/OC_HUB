'use client'

import { useState } from 'react'
import { 
  Users, 
  UserPlus, 
  Shield, 
  Mail,
  Calendar,
  MoreVertical,
  Trash2,
  Edit
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// Placeholder user data
const placeholderUsers = [
  {
    id: '1',
    email: 's.falasi@gmail.com',
    role: 'admin',
    createdAt: '2024-01-01T00:00:00Z',
    lastSignIn: '2024-01-04T10:00:00Z'
  },
]

export default function UsersManagementPage() {
  const [users] = useState(placeholderUsers)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage platform users and permissions
          </p>
        </div>
        <Button onClick={() => setShowInviteForm(!showInviteForm)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Invite User
        </Button>
      </div>

      {/* Invite Form */}
      {showInviteForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Invite New User
            </CardTitle>
            <CardDescription>
              Send an invitation email to add a new user
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                type="email"
                placeholder="user@example.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="flex-1"
              />
              <Button disabled>
                <Mail className="h-4 w-4 mr-2" />
                Send Invite (Coming Soon)
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Note: New users will have read-only access by default. Admin privileges must be granted separately.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Users List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Platform Users
          </CardTitle>
          <CardDescription>
            {users.length} user{users.length !== 1 ? 's' : ''} registered
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {users.map((user) => (
              <div 
                key={user.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="font-semibold">
                      {user.email.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{user.email}</span>
                      {user.role === 'admin' && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-purple-500/10 text-purple-500 text-xs rounded">
                          <Shield className="h-3 w-3" />
                          Admin
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Joined {new Date(user.createdAt).toLocaleDateString()}
                      </span>
                      <span>
                        Last active {new Date(user.lastSignIn).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon" disabled>
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" disabled>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Role Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>User Roles</CardTitle>
          <CardDescription>
            Understanding permission levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-5 w-5 text-blue-500" />
                <h4 className="font-semibold">User</h4>
              </div>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Access chat with all reports</li>
                <li>• Browse report library</li>
                <li>• View data bank</li>
                <li>• Generate meeting briefs</li>
                <li>• Analyze news articles</li>
              </ul>
            </div>
            <div className="p-4 border rounded-lg border-purple-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="h-5 w-5 text-purple-500" />
                <h4 className="font-semibold">Admin</h4>
              </div>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• All user permissions</li>
                <li>• Upload new reports</li>
                <li>• Manage users</li>
                <li>• Access processing queue</li>
                <li>• View system status</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
