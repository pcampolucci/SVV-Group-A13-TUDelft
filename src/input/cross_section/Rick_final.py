



tau_1, tau_2, tau_3, tau_4, tau_5, tau_6 = Shear_stress_due_to_shear(qb1, qb2,qb3,qb4,qb5,qb6,t_sk,t_sp)


#Calculate the twist of the aileron after calculating the shear flow due to torsion and the twist rate at each spanwise location

T_lst = [-2,-1,-3]   #change to actual torque distribution along the span for a number of points based on Willems code   
G = 28e9  #shear modulus of the aileron
def Twist_of_aileron(T_lst,per_semicircle, per_triangle,t_sk,t_sp,h,l_a,A1,A2):    #Solves a set of 3 equations for unit torque applied, output q1, q2 and twsit_rate_times_G
    #For T_lst use the value of the torque at each location, for examply for adding a loop or using input out of a list of torques
    #For verification, one can change the perimiter of the circle and triangle by chaning the geometry and calculate the q1,q2 and twist rate and see wheter it makes sense or not
    #After computing twist rate, take distance from hinge line to shear center to compute the deflection of the hinge line
    k = 1/(2*A1) * (per_semicircle/t_sk + 2*h/t_sp) 
    l = 1/(2*A1)*-2*h/t_sp
    m = 1/(2*A2)*-2*h/t_sp
    n = 1/(2*A2) * (per_triangle/t_sk + 2*h/t_sp)
    B = np.array([[2*A1,2*A2,0],[k,l,-1],[m,n,-1]])
    twist_rate_lst = []
    q1_lst = []
    q2_lst = []
    x_theta_0 = l_a/2  #due to assumption around x, x_sc in middle [m]
    theta_0 = 0       #this is a boundary condition [rad]
    for i in range(len(T_lst)):
        w = np.array([T_lst[i],0,0])
        solution = np.linalg.solve(B,w)
        q1 = solution[0]
        q2 = solution[1]
        q1_lst.append(q1)
        q2_lst.append(q2)
        twist_rate_times_G = solution[2]
        twist_rate = twist_rate_times_G / G 
        twist_rate_lst.append(twist_rate)
    J = T_lst[-1] / twist_rate_times_G              #calculate the J for a combination of torque and twist rate
    dx = l_a/(len(T_lst)-1)         #step in x direction between the points where the torque is computed and thus where twist_rate is known
    n_steps = math.floor(x_theta_0/dx)      #number of full steps untill location of boundary condition reached, returns an integer
    twist_before_bc = sum([twist_rate_lst[j] for j in range(n_steps)]) * dx + theta_0       #twist of first section
    twist_lst = [twist_before_bc]
    twist_after_bc = 0
    for i in range(1,len(T_lst)):
        if i < n_steps:
            twist_before_bc = twist_before_bc - twist_rate_lst[i-1]*dx       #compute the twist of each section between two points (positive for positive twist rate)
            twist_lst.append(twist_before_bc)
            
        if i == n_steps:                                  #this is the section where the boundary condition is applied
            twist_lst.append(theta_0)                     #now the section of the boundary condition is reached, this entire section attains this value (neglecting the twist along the even smaller subsection if point of boundary condition falls in between two points)
        if i > n_steps:
            twist_after_bc = twist_after_bc + twist_rate_lst[i]*dx     #or -, plot if torque distribution is known. At the boundary condition, the sign of the twist should change 
            twist_lst.append(twist_after_bc)
    return q1_lst,q2_lst, J, twist_rate_lst, twist_lst         #J, twist rate and twist at every x location taken 
    
q1_lst, q2_lst, J, twist_rate_lst, twist_lst = Twist_of_aileron(T_lst,per_semicircle, per_triangle,t_sk,t_sp,h,l_a,A1,A2)



def Shear_stress_due_to_torsion(q1,q2,t_sk,t_sp):   
    tau_skin_cell_1_lst = [q1[i]/t_sk for i in range(len(q1))]
    tau_skin_cell_2_lst = [q2[i]/t_sk for i in range(len(q1))]
    tau_spar_lst = [(q2[i]-q1[i])/t_sp for i in range(len(q1))]
        
    return tau_skin_cell_1_lst, tau_skin_cell_2_lst, tau_spar_lst

tau_skin_cell_1_lst, tau_skin_cell_2_lst, tau_spar_lst = Shear_stress_due_to_torsion(q1_lst,q2_lst,t_sk,t_sp)

def Total_shear_stress(tau_1,tau_2,tau_3,tau_4,tau_5,tau_6, tau_skin_cell_1_lst,tau_skin_cell_2_lst,tau_spar_lst):
    """Calculates the total shear stress distribution tau_yz per section for every x location along the span and puts this in a list, so 6 lists for each spanwise location
       it returns a list of lists with every list a shear stress distribution at a specific x location.""" 
    total_shear_stress_distribution_at_every_x_loc = []
    for j in range(len(tau_skin_cell_1_lst)):
        tau_total_1_at_x_loc = [tau_1[i] + tau_skin_cell_1_lst[j] for i in range(len(tau_1))]
        tau_total_2_at_x_loc = [tau_2[i] + tau_spar_lst[j] for i in range(len(tau_2))]
        tau_total_3_at_x_loc = [tau_3[i] + tau_skin_cell_2_lst[j] for i in range(len(tau_3))]
        tau_total_4_at_x_loc = [tau_4[i] + tau_skin_cell_2_lst[j] for i in range(len(tau_4))]
        tau_total_5_at_x_loc = [tau_5[i] + tau_spar_lst[j] for i in range(len(tau_5))]
        tau_total_6_at_x_loc = [tau_6[i] + tau_skin_cell_1_lst[j] for i in range(len(tau_6))]
        total_shear_stress_distribution_at_every_x_loc.append(tau_total_1_at_x_loc + tau_total_2_at_x_loc + tau_total_3_at_x_loc + tau_total_4_at_x_loc + tau_total_5_at_x_loc + tau_total_6_at_x_loc)
    return total_shear_stress_distribution_at_every_x_loc  #example output[0] = shear stress distribution at first x location along the span, in the order of the sections 1,2,3,4,5,6

total_shear_stress_distribution_at_every_x_loc = Total_shear_stress(tau_1,tau_2,tau_3,tau_4,tau_5,tau_6, tau_skin_cell_1_lst,tau_skin_cell_2_lst,tau_spar_lst)


My = 1          #to be changed and computed by a function in Willems code, just a single value for a spefic x location
Mz = 1          #to be changed computed by a function in Willems code, just a single value for a spefic x location

#def Direct_stress_distribution(Mz,My,Iyy,Izz,zc,yco1,zco1,yco2,zco2,yco3,zco3,yco4,zco4,yco5,zco5,yco6,zco6):     #for a unit moment in x and y direction
#    """Computes the Direct stress distrubtion along the cross-section at each middle point of a section where the shear flow is calculated based on the Mx and My of a specific location along the span"""
#    sigma_xx_1 = [My*((zco1[i]+zco1[i+1])/2 - zc)/Iyy + Mz*(yco1[i]+yco1[i+1])/2 for i in range(len(zco1)-1)]            #zc is zlocation of centroid, compute y- and z-location of the middle of each section where the shear flow is computed
#    sigma_xx_2 = [My*((zco2[i]+zco2[i+1])/2 - zc)/Iyy + Mz*(yco2[i]+yco2[i+1])/2 for i in range(len(zco2)-1)]
#    sigma_xx_3 = [My*((zco3[i]+zco3[i+1])/2 - zc)/Iyy + Mz*(yco3[i]+yco3[i+1])/2 for i in range(len(zco3)-1)]
#    sigma_xx_4 = [My*((zco4[i]+zco4[i+1])/2 - zc)/Iyy + Mz*(yco4[i]+yco4[i+1])/2 for i in range(len(zco4)-1)]
#    sigma_xx_5 = [My*((zco5[i]+zco5[i+1])/2 - zc)/Iyy + Mz*(yco5[i]+yco5[i+1])/2 for i in range(len(zco5)-1)]
#    sigma_xx_6 = [My*((zco6[i]+zco6[i+1])/2 - zc)/Iyy + Mz*(yco6[i]+yco6[i+1])/2 for i in range(len(zco6)-1)]
#    sigma_xx_1.extend(sigma_xx_2 + sigma_xx_3 + sigma_xx_4 + sigma_xx_5 + sigma_xx_6)       #combine all section to get distribution in one list
#    return sigma_xx_1
#direct_stress_distribution = Direct_stress_distribution(Mz,My,Iyy,Izz,zc,yco1,zco1,yco2,zco2,yco3,zco3,yco4,zco4,yco5,zco5,yco6,zco6)
def Direct_stress_distribution(Mz,My,Iyy,Izz,zc,yco1,zco1,yco2,zco2,yco3,zco3,yco4,zco4,yco5,zco5,yco6,zco6):     #for a unit moment in x and y direction
    """Computes the Direct stress distrubtion along the cross-section at each point where the shear flow is calculated based on the Mx and My of a specific location along the span"""
    sigma_xx_1 = [My*(zco1[i] - zc)/Iyy + Mz*yco1[i] for i in range(len(zco1))]            #zc is zlocation of centroid, compute y- and z-location of the middle of each section where the shear flow is computed
    sigma_xx_2 = [My*(zco2[i] - zc)/Iyy + Mz*yco2[i] for i in range(len(zco2))]
    sigma_xx_3 = [My*(zco3[i] - zc)/Iyy + Mz*yco3[i] for i in range(len(zco3))]
    sigma_xx_4 = [My*(zco4[i]- zc)/Iyy + Mz*yco4[i] for i in range(len(zco4))]
    sigma_xx_5 = [My*(zco5[i] - zc)/Iyy + Mz*yco5[i] for i in range(len(zco5))]
    sigma_xx_6 = [My*(zco6[i] - zc)/Iyy + Mz*yco6[i] for i in range(len(zco6))]
    sigma_xx_1.extend(sigma_xx_2 + sigma_xx_3 + sigma_xx_4 + sigma_xx_5 + sigma_xx_6)       #combine all section to get distribution in one list
    return list(sigma_xx_1)
direct_stress_distribution = Direct_stress_distribution(Mz,My,Iyy,Izz,zc,yco1,zco1,yco2,zco2,yco3,zco3,yco4,zco4,yco5,zco5,yco6,zco6)


#Calculation of the Von-Mises stress distribution
#assume tau xy tau xz are neglegible compared to the shear acting in the yz plane, same for sigma_yy and sigma_zz --> calculation of von mises stress simplifies
tau_xy = 0
tau_xz = 0
sigma_yy = 0
sigma_zz = 0


n = len(T_lst)  #This should be changed to the variable that defines the number of points taken where the loads are discretised along the span including begin and end points, in my program it matches the size of the torque list but that also changes according to the number of points along x chosen
def Von_Mises_stress_distribution(direct_stress_distribution,shear_stress_distribution,n):     #use total shear stresses!
    """This function calculates the Von Mises stress distrubtion for every x-location taken along the span, based on the direct stress calculation and the total shear stress calculation"""
    sigma_vm_distribution_at_every_x_loc = []
    for j in range(n):
        sigma_vm = [np.sqrt(direct_stress_distribution[i]**2 + 3*shear_stress_distribution[n-1][i]**2) for i in range(len(direct_stress_distribution))]
        sigma_vm_distribution_at_every_x_loc.append(sigma_vm)
    return sigma_vm_distribution_at_every_x_loc  #example sigma_vm_distribution[0] is the distribution at the first x-location taken along the span

Von_Mises_stress_distribution_at_every_x_loc = Von_Mises_stress_distribution(direct_stress_distribution,total_shear_stress_distribution_at_every_x_loc,n)

print()

#-------------------------------------------------------------------------------------------------------------------------------------------------

#for i,j in zip([yco2,yco3,yco4,yco5,yco6],[zco2,zco3,zco4,zco5,zco6]):
#    yco1.extend(i)
#    zco1.extend(j)
#  
#
#def plot_shearflow(zco,yco,Von_Mises_stress_distribution_at_every_x_loc):
#    n = 2           #distribution calculated at first point
#    plt.scatter(zco1,yco1,c=Von_Mises_stress_distribution_at_every_x_loc[n],cmap='jet')
#    plt.xlabel('z[m]', fontsize=16)
#    plt.ylabel('y[m]', fontsize=16)
#    #plt.legend()
#    c=plt.colorbar()
#    c.set_label('Von Mises Stress [N/m^2]')
#    plt.title('Von Mises Stress Distribution')
#    #plt.savefig("flow.png")
#    plt.show()
#plot_shearflow(zco1,yco1,Von_Mises_stress_distribution_at_every_x_loc)





