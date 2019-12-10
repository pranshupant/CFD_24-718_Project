import numpy as np 
from numba import jit
from Initialize import *
from Animation import *
from contour import *
import copy

def timer(t1):
    # print(time.time()-t1)
    return time.time()


@jit(nopython=True)
def transport(T,u,v,dt,dx,dy,alpha):
    nx = T.shape[0]-1
    ny = T.shape[1]-1

    T_ = np.zeros(T.shape)
    def RHS(alpha,T,dx,dy,i,j):
        rx_top=dx[(i,j)]-dx[(i-1,j)]
        rx_bot=dx[(i,j)]+dx[(i-1,j)]
        rx = rx_top/rx_bot
        
        ry_top=dy[(i,j)]-dy[(i,j-1)]
        ry_bot=dy[(i,j)]+dy[(i,j-1)]
        ry = ry_top/ry_bot

        T2_x=((1+rx)*T[(i+1,j)]-2*T[(i,j)]+(1-rx)*T[(i-1,j)])/((dx[(i,j)]**2+dx[(i-1,j)]**2)/2)
        T2_y=((1+ry)*T[(i,j+1)]-2*T[(i,j)]+(1-ry)*T[(i,j-1)])/((dy[(i,j)]**2+dy[(i,j-1)]**2)/2)

        rhs=alpha*(T2_x+T2_y)

        return rhs

    def Der_1(u,v,T,dx,dy,i,j):
        duTdx=(u[(i,j)]*(T[(i+1,j)]+T[(i,j)])-u[(i-1,j)]*(T[(i,j)]+T[(i-1,j)]))/dx[(i,j)]/2
        dvTdy=(v[(i,j)]*(T[(i,j+1)]+T[(i,j)])-v[(i,j-1)]*(T[(i,j)]+T[(i,j-1)]))/dy[(i,j)]/2

        return duTdx, dvTdy

    for i in range(1,nx):
        for j in range(1,ny):
            rhs = RHS(alpha,T,dx,dy,i,j)
            duTdx,dvTdy=Der_1(u,v,T,dx,dy,i,j)
            T_[(i,j)]=T[(i,j)]+dt*(rhs-duTdx-dvTdy)
    return T_

@jit(nopython=True)
def poisson(P,u,v,dt,dx,dy,rho):
    # u and v are from the "predictor step"
    # P comes from the previous time step
    nx = P.shape[0]-1
    ny = P.shape[1]-1
    def Frac(dx,dy,i,j):
        rx_top=dx[(i,j)]-dx[(i-1,j)]
        rx_bot=dx[(i,j)]+dx[(i-1,j)]
        rx = rx_top/rx_bot
        
        ry_top=dy[(i,j)]-dy[(i,j-1)]
        ry_bot=dy[(i,j)]+dy[(i,j-1)]
        ry = ry_top/ry_bot

        frac_x=4/(dx[(i,j)]**2+dx[(i-1,j)]**2)
        frac_y=4/(dy[(i,j)]**2+dy[(i,j-1)]**2)
        Rx_p=2*(1+rx)/(dx[(i,j)]**2+dx[(i-1,j)]**2)
        Rx_n=2*(1-rx)/(dx[(i,j)]**2+dx[(i-1,j)]**2)
        Ry_p=2*(1+ry)/(dy[(i,j)]**2+dy[(i,j-1)]**2)
        Ry_n=2*(1-ry)/(dy[(i,j)]**2+dy[(i,j-1)]**2)
        return frac_x, frac_y, Rx_p, Rx_n, Ry_p, Ry_n

    def RHS(u,v,dx,dy,i,j,dt,rho):
        U_=(u[(i,j)]-u[(i-1,j)])/dx[(i-1,j)]
        V_=(v[(i,j)]-v[(i,j-1)])/dy[(i,j-1)]
        
        rhs=rho/dt*(U_+V_)
        return rhs

    Con = 1e-6
    err = 1
    k = 0
    while (err>Con):
        # temp = copy.deepcopy(P)
        temp=P
        k+=1
        for i in range(1,nx):
            for j in range(1,ny):
                frac_x,frac_y,Rx_p,Rx_n,Ry_p,Ry_n=Frac(dx,dy,i,j)
                rhs = RHS(u,v,dx,dy,i,j,dt,rho)
                
                P[(i,j)]=(frac_x+frac_y)**(-1)*((Rx_p*P[(i+1,j)]+Rx_n*P[(i-1,j)])+(Ry_p*P[(i,j+1)]+Ry_n*P[(i,j-1)])-rhs)
        if k == 100000:# Look into this
            print('not converged', err)
            break
        err = np.max(np.abs(P-temp))
    return P

@jit(nopython=True)
def Adv(u, v, x, y, i, j, flag): 
    x_1 = x[(i,j)] 
    x_0 = x[(i-1,j)]

    y_1 = y[(i,j)] 
    y_0 = y[(i,j-1)]

    # u_1 = np.zeros((u.shape[0], u.shape[1]))
    # u_2 = np.zeros((u.shape[0], u.shape[1]))

    # v_1 = np.zeros((v.shape[0], v.shape[1]))
    # v_2 = np.zeros((v.shape[0], v.shape[1]))

    if flag == 0:
        u_1 = u[i][j]*(u[i+1][j] - u[i-1][j])/(x_0 + x_1)
        u_2 = 0.25*(v[i-1][j]+v[i][j]+v[i-1][j+1]+ v[i][j+1])*(u[i][j+1] - u[i][j-1])/(y_0 + y_1)

        return u_1 + u_2

    if flag == 1:
        v_1 = v[i][j]*(v[i][j+1] - v[i][j-1])/(y_0 + y_1)
        v_2 = 0.25*(u[i][j-1]+u[i][j]+u[i+1][j-1]+ u[i+1][j])*(v[i+1][j] - v[i-1][j])/(x_0 + x_1)

        return v_1 + v_2

@jit(nopython=True)
def Diff(u, x, y, i, j):

    # u_1 = np.zeros((u.shape[0], u.shape[1]))
    # u_2 = np.zeros((u.shape[0], u.shape[1]))

    x_1 = x[(i,j)] 
    x_0 = x[(i-1,j)]

    y_1 = y[(i,j)] 
    y_0 = y[(i,j-1)]

    r_x = (x_1 - x_0)/(x_0 + x_1)
    r_y = (y_1 - y_0)/(y_0 + y_1)

    u_1 = 2*((1-r_x)*u[i-1][j] - 2*u[i][j] + (1+r_x)*u[i+1][j])/(x_0**2 + x_1**2)#x[(i,j)]**2)
    u_2 = 2*((1-r_y)*u[i][j-1] - 2*u[i][j] + (1+r_y)*u[i][j+1])/(y_0**2 + y_1**2)#(y[(i,j)]**2)

    return u_1 + u_2

@jit(nopython=True)
def predictor(x, y, u, v, T, dt, T_ref, rho, g, nu, beta):
    # Main Predictor Loop
    nx = T.shape[0]
    ny = T.shape[1]

    #print(v.shape[0], v.shape[1])

    u_ = np.zeros((u.shape[0], u.shape[1]))
    v_ = np.zeros((v.shape[0], v.shape[1]))

    # u_ = copy.deepcopy(u)
    # v_ = copy.deepcopy(v)

    u_=u
    v_=v
    #print('*******')
    #print(nx, ny)


    for i in range(1, nx-1):
        for j in range(1, ny-1):
            #print(i,j)
            u_[i][j] = u[i][j] + dt*(nu*(Diff(u, x, y, i, j)) - Adv(u, v, x, y, i, j, 0))

            v_[i][j] = v[i][j] + dt*(nu*(Diff(v, x, y, i, j)) - Adv(u, v, x, y, i, j, 1))#+ rho*g*beta*(0.5*(T[i][j-1] + T[i][j+1])-T_ref)) #Add Bousinessq Terms  
    
    return u_, v_

@jit(nopython=True)
def corrector(x, y, u, v, p, dt, rho):

    nx = p.shape[0]
    ny = p.shape[1]


    u_ = np.zeros((u.shape[0], u.shape[1]))
    v_ = np.zeros((v.shape[0], v.shape[1]))

    # u_ = copy.deepcopy(u)
    # v_ = copy.deepcopy(v)

    u_=u
    v_=v

    for i in range(1, nx-1):
        for j in range(1, ny-1):

            x_1 = x[(i,j)] 
            x_0 = x[(i-1,j)]
            y_1 = y[(i,j)] 
            y_0 = y[(i,j-1)]

            u_[i][j] = u[i][j] - (dt/rho)*(p[i+1][j] - p[i][j])/(x_1 + x_0)
            v_[i][j] = v[i][j] - (dt/rho)*(p[i][j+1] - p[i][j])/(y_1 + y_0)
    
    return u_, v_

# @jit(nopython=True)
def BC_update(u, v, p, T):
    nx = p.shape[0]-1
    ny = p.shape[1]-1
    #inlet
    #v[0,:] = v[1,:]
    v[0,:] = copy.deepcopy(-v[1,:])

    p[0,:] = copy.deepcopy(p[1,:])
    T[0,:] = copy.deepcopy(T[1,:])

    #bottom
    u[:,0] =  copy.deepcopy(-u[:,1])

    v[:,0] = 0.

    p[:,0] = copy.deepcopy(p[:,1])
    T[:,0] = copy.deepcopy(T[:,1])

    #outlet
    u[nx-1,:] = copy.deepcopy(u[nx-2,:])
    u[nx,:] = copy.deepcopy(u[nx-1,:])

    v[nx,:] = copy.deepcopy(v[nx-1,:])
    p[nx-1,:] = copy.deepcopy(p[nx,:])
    T[nx,:] = copy.deepcopy(T[nx-1,:])

    #top
    u[:,ny] =  copy.deepcopy(u[:,ny-1])
    # u[:,ny] = 2.
    # u[:,ny-1] = 2.
    # u[:,ny] = copy.deepcopy(-u[:,ny-1])

    # v[:,ny-1] =  copy.deepcopy(v[:,ny-2])
    # v[:,ny] =  copy.deepcopy(v[:,ny-1])
    v[:,ny] = 0.
    v[:,ny-1] = 0.


    p[:,ny] = copy.deepcopy(p[:,ny-1])
    T[:,ny] = copy.deepcopy(T[:,ny-1])

    
    T[20,5] = 325

    return u, v, p, T



#@numba.jit(nopython=True, parallel=True)
def main():
    rho = 1.225
    T_ref = 300
    beta = 1./300
    nu = 1.569e-3
    alpha_T = 2.239e-5
    alpha_pollutant = 2.239e-5
    total_t = 1
    t = 0
    dt = 0.0001
    g = 9.81

    initialize()

    x,y = read_delta(0)
    P, T, u, v = read_all_scalar(0)
    print(P.shape) 
    #print(T.shape[0], T.shape[1])

    running = True
    while running:
        if int(t/dt)%1000==0:
            print('\ntime=%.3f'%t)
            #if t!=0:
            write_all_scalar(P, T, u, v, t)
            # sys.exit()
        t1=time.time()
        
        u_, v_ = predictor(x, y, u, v, T, dt, T_ref, rho, g, nu, beta)
        t1=timer(t1)
        #print(u_)
        p_new = poisson(P,u_,v_,dt,x,y,rho)
        t1=timer(t1)
        #p_new = copy.deepcopy(P)
        #print(p_new)
        u_new, v_new = corrector(x, y, u_, v_, p_new, dt, rho)
        t1=timer(t1)
        #print(u_new)
        T_new = transport(T,u_new,v_new,dt,x,y,alpha_T)
        #T_new = np.zeros(T.shape)
        #print(T_new)
        #phi_new = transport(phi,u,v,dt,x,y,alpha_pollutant) #Pollutant Transport

        u_new, v_new, p_new, T_new = copy.deepcopy(BC_update(u_new, v_new, p_new, T_new))
        
        u = copy.deepcopy(u_new)
        v = copy.deepcopy(v_new)

        P = copy.deepcopy(p_new)
        T = copy.deepcopy(T_new)

        t += dt
        #sys.exit()
        # write_all_scalar(P, T, u_new, v_new, t)
        
        if t >= total_t:
            write_all_scalar(P, T, u_new, v_new, t)
            running = False
    Contour('U',grid='yes')
    Contour('V',grid='yes')
    Contour('P',grid='yes')
    Streamlines('U','V',grid='yes')

    Contour('T')
    # print(u)


if __name__ == '__main__':
    main()