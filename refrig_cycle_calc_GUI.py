"""
By: Alex Kalmbach

Description: This program provides thermodynamic information in the form of a GUI on the performance of a refrigeration cycle.
The user specifies the refrigerant they want to use as well as desired temperatures, pressures, and compressor
isentropic efficiency.
The CoolProp Library is used to get properties of the refrigerant at different points in the cycle, which are
ultimately used to calculate the heat removed, heat rejected, work input, and the cycle efficiency.

Sources:
[1] Thermodynamics An Engineering Approach (Cengel & Boles 8th Edition)
[2] Danfoss CoolSelector2

Date: 02/19/2025 (ver 1.0)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import CoolProp.CoolProp as CP
from pint import UnitRegistry

ureg = UnitRegistry()
ureg.define("Rankine = 1.8 * kelvin = R")
ureg.define("lbm = pound")
Q_ = ureg.Quantity

def convert_to_si(property_name: str, value: float) -> float:
    """
    Convert from IP units to SI units for the given property.
    """
    conversions = {
        "T":  ureg.Quantity(value, "degF").to("kelvin").magnitude,   # °F -> K
        "P":  ureg.Quantity(value, "psi").to("pascal").magnitude,    # psia -> Pa
        "H":  ureg.Quantity(value, "Btu/lbm").to("J/kg").magnitude,  # BTU/lb -> J/kg
        "S":  ureg.Quantity(value, "Btu/(lbm*degF)").to("J/(kg*K)").magnitude,
        "M":  ureg.Quantity(value, "lbm/min").to("kg/s").magnitude,  # lb/min -> kg/s
    }
    return conversions.get(property_name, value)

def convert_from_si(property_name: str, value: float) -> float:
    """
    Convert from SI units back to IP units for printing.
    """
    conversions = {
        "T":    ureg.Quantity(value, "kelvin").to("degF").magnitude,
        "P":    ureg.Quantity(value, "pascal").to("psi").magnitude,
        "H":    ureg.Quantity(value, "J/kg").to("Btu/lbm").magnitude,
        "S":    ureg.Quantity(value, "J/(kg*K)").to("Btu/(lbm*degF)").magnitude,
        "D":    ureg.Quantity(value, "kg/m^3").to("lbm/ft^3").magnitude,
        "Heat": ureg.Quantity(value, "watt").to("BTU/hr").magnitude,  # W -> BTU/hr
    }
    return conversions.get(property_name, value)

class RefrigerationCycleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Refrigeration Cycle Simulator")

        # Menu bar & About
        self.menu_bar = tk.Menu(self.root)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_info)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.root.config(menu=self.menu_bar)

        # Choices
        self.refrigerants = ["R22", "R134a", "R32", "R410A", "R507A"]
        self.ref_states   = ["ASHRAE", "NBP", "IIR"]

        # Attempt to load and scale image
        try:
            original_logo = tk.PhotoImage(file="pressure_enthalpy_diagram.png")
            # scale down the image by factor of 2
            self.logo = original_logo.subsample(2, 2)
        except Exception as e:
            print(f"Could not load image: {e}")
            self.logo = None

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(sticky="nsew")

        # Left sub-frame for all input widgets
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky="nw")

        # Heading
        heading_label = ttk.Label(
            input_frame,
            text="Refrigeration Cycle Calculator",
            font=("Helvetica", 10, "bold")
        )
        heading_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Row 1: Select Refrigerant
        ttk.Label(input_frame, text="Select Refrigerant:").grid(row=1, column=0, sticky=tk.W)
        self.refrigerant_var = tk.StringVar(value=self.refrigerants[0])
        self.refrigerant_menu = ttk.Combobox(
            input_frame,
            textvariable=self.refrigerant_var,
            values=self.refrigerants,
            width=14
        )
        self.refrigerant_menu.grid(row=1, column=1, sticky=tk.W)

        # Row 2: Reference State label
        ttk.Label(input_frame, text="Select Reference State:").grid(row=2, column=0, sticky=tk.W)

        # Sub-frame for combo + "?"
        ref_state_frame = ttk.Frame(input_frame)
        ref_state_frame.grid(row=2, column=1, sticky=tk.W)

        self.ref_state_var = tk.StringVar(value=self.ref_states[0])
        self.ref_state_menu = ttk.Combobox(
            ref_state_frame,
            textvariable=self.ref_state_var,
            values=self.ref_states,
            width=14
        )
        self.ref_state_menu.pack(side=tk.LEFT)

        info_button = ttk.Button(
            ref_state_frame,
            text="?",
            width=2,
            command=self.show_ref_state_info
        )
        info_button.pack(side=tk.LEFT, padx=(5, 0))

        # Row 3-4: Evaporator Input
        ttk.Label(input_frame, text="Evaporator Input Type:").grid(row=3, column=0, sticky=tk.W)
        self.evap_choice = tk.StringVar(value="Pressure (psia)")
        self.evap_menu = ttk.Combobox(
            input_frame, textvariable=self.evap_choice,
            values=["Pressure (psia)", "Temperature (°F)"]
        )
        self.evap_menu.grid(row=3, column=1, sticky=tk.W)

        ttk.Label(input_frame, text="Evaporator Value:").grid(row=4, column=0, sticky=tk.W)
        self.evap_entry = ttk.Entry(input_frame)
        self.evap_entry.grid(row=4, column=1, sticky=tk.W)

        # Row 5-6: Condenser Input
        ttk.Label(input_frame, text="Condenser Input Type:").grid(row=5, column=0, sticky=tk.W)
        self.cond_choice = tk.StringVar(value="Pressure (psia)")
        self.cond_menu = ttk.Combobox(
            input_frame, textvariable=self.cond_choice,
            values=["Pressure (psia)", "Temperature (°F)"]
        )
        self.cond_menu.grid(row=5, column=1, sticky=tk.W)

        ttk.Label(input_frame, text="Condenser Value:").grid(row=6, column=0, sticky=tk.W)
        self.cond_entry = ttk.Entry(input_frame)
        self.cond_entry.grid(row=6, column=1, sticky=tk.W)

        # Row 7-10: Superheat, Subcooling, Efficiency, Flow
        ttk.Label(input_frame, text="Superheat (°F):").grid(row=7, column=0, sticky=tk.W)
        self.superheat_entry = ttk.Entry(input_frame)
        self.superheat_entry.grid(row=7, column=1, sticky=tk.W)

        ttk.Label(input_frame, text="Subcooling (°F):").grid(row=8, column=0, sticky=tk.W)
        self.subcooling_entry = ttk.Entry(input_frame)
        self.subcooling_entry.grid(row=8, column=1, sticky=tk.W)

        ttk.Label(input_frame, text="Compressor Isentropic Efficiency (%):").grid(row=9, column=0, sticky=tk.W)
        self.efficiency_entry = ttk.Entry(input_frame)
        self.efficiency_entry.grid(row=9, column=1, sticky=tk.W)

        ttk.Label(input_frame, text="Mass Flow Rate (lb/min):").grid(row=10, column=0, sticky=tk.W)
        self.mass_flow_entry = ttk.Entry(input_frame)
        self.mass_flow_entry.grid(row=10, column=1, sticky=tk.W)

        # Row 11: Calculate Button
        self.calculate_button = ttk.Button(input_frame, text="Calculate", command=self.calculate)
        self.calculate_button.grid(row=11, column=0, columnspan=3, pady=10)

        # =========================
        # Row 12: Output + Image side-by-side
        # =========================
        output_frame = ttk.Frame(input_frame)
        output_frame.grid(row=12, column=0, columnspan=3, sticky="nw")

        # Place the text output
        self.output_text = tk.Text(output_frame, height=25, width=80, font=("Courier", 11))
        self.output_text.grid(row=0, column=0, rowspan=2, sticky="nw")

        # If the image was loaded, align it with the top of the output table
        if self.logo is not None:
            # Place the image
            self.logo_label = ttk.Label(output_frame, image=self.logo)
            self.logo_label.grid(row=0, column=1, sticky="n", padx=(5, 0))

            # Add a title **centered** directly below the image
            self.image_title = ttk.Label(output_frame, text="Fig 1: Refrigeration Cycle Pressure-Enthalpy Diagram",
                                         font=("Helvetica", 10))
            self.image_title.grid(row=1, column=1, sticky="n", pady=(0, 0))  # No extra space

        # Row 13: Author Credit
        self.author_label = ttk.Label(input_frame, text="Developed in Python by Alex Kalmbach", foreground="grey")
        self.author_label.grid(row=13, column=2, sticky=tk.E, pady=(5, 0))

    def show_info(self):
        info_text = (
            "Refrigeration Cycle Simulator\n\n"
            "This program calculates the performance of a refrigeration cycle "
        )
        messagebox.showinfo("About Refrigeration Cycle Simulator", info_text)

    def show_ref_state_info(self):
        ref_text = (
            "Refrigeration Cycle Simulator\n\n"
            "This program calculates the performance of a refrigeration cycle "
        )
        messagebox.showinfo("Reference State Info", ref_text)

    def calculate(self):
        """
        Fully implements the cycle calculation logic:
        - Gather inputs
        - Convert to SI
        - Use CoolProp to get state points
        - Compute performance metrics
        - Output results in the text area
        """
        try:
            # Collect user inputs
            refrigerant   = self.refrigerant_var.get()
            ref_state     = self.ref_state_var.get()
            evap_type     = self.evap_choice.get()
            evap_value    = float(self.evap_entry.get())
            cond_type     = self.cond_choice.get()
            cond_value    = float(self.cond_entry.get())
            superheat_F   = float(self.superheat_entry.get())
            subcooling_F  = float(self.subcooling_entry.get())
            isentropic_eff = float(self.efficiency_entry.get())
            mass_flow_lb_min = float(self.mass_flow_entry.get())

            # Validate numeric ranges
            if not (0 <= superheat_F <= 30):
                raise ValueError("Superheat must be 0-30 °F.")
            if not (0 <= subcooling_F <= 30):
                raise ValueError("Subcooling must be 0-30 °F.")
            if not (20 <= isentropic_eff <= 100):
                raise ValueError("Isentropic efficiency must be 20-100.")
            if mass_flow_lb_min <= 0:
                raise ValueError("Mass flow rate must be positive.")

        except ValueError as err:
            messagebox.showerror("Input Error", f"Invalid input: {err}")
            return

        # Set reference state
        CP.set_reference_state(refrigerant, ref_state)

        # Convert isentropic efficiency to fraction
        isentropic_eff /= 100.0

        # Evaporator side
        if "Pressure" in evap_type:
            low_pressure = convert_to_si("P", evap_value)
            sat_evap_T   = CP.PropsSI('T', 'P', low_pressure, 'Q', 1, refrigerant)
        else:
            sat_evap_T   = convert_to_si("T", evap_value)
            low_pressure = CP.PropsSI('P', 'T', sat_evap_T, 'Q', 1, refrigerant)

        # Condenser side
        if "Pressure" in cond_type:
            high_pressure = convert_to_si("P", cond_value)
            sat_cond_T    = CP.PropsSI('T', 'P', high_pressure, 'Q', 1, refrigerant)
        else:
            sat_cond_T    = convert_to_si("T", cond_value)
            high_pressure = CP.PropsSI('P', 'T', sat_cond_T, 'Q', 1, refrigerant)

        # Convert superheat & subcooling from °F to K
        superheat_K  = max(0.0001, superheat_F  * 5.0/9.0)
        subcooling_K = max(0.0001, subcooling_F * 5.0/9.0)
        mass_flow    = convert_to_si("M", mass_flow_lb_min)

        # STATE POINTS
        # 1: Evaporator Exit
        T1 = sat_evap_T + superheat_K
        H1 = CP.PropsSI('H', 'P', low_pressure, 'T', T1, refrigerant)
        S1 = CP.PropsSI('S', 'P', low_pressure, 'T', T1, refrigerant)
        D1 = CP.PropsSI('D', 'P', low_pressure, 'T', T1, refrigerant)

        # 2: Compressor Exit
        h2s_ideal = CP.PropsSI('H', 'P', high_pressure, 'S', S1, refrigerant)
        H2 = H1 + (h2s_ideal - H1) / isentropic_eff
        T2 = CP.PropsSI('T', 'P', high_pressure, 'H', H2, refrigerant)
        S2 = CP.PropsSI('S', 'P', high_pressure, 'H', H2, refrigerant)
        D2 = CP.PropsSI('D', 'P', high_pressure, 'H', H2, refrigerant)

        # 3: Condenser Exit
        Tcond_sat = CP.PropsSI('T', 'P', high_pressure, 'Q', 0, refrigerant)
        T3 = Tcond_sat - subcooling_K
        H3 = CP.PropsSI('H', 'P', high_pressure, 'T', T3, refrigerant)
        S3 = CP.PropsSI('S', 'P', high_pressure, 'T', T3, refrigerant)
        D3 = CP.PropsSI('D', 'P', high_pressure, 'T', T3, refrigerant)

        # 4: Expansion Valve
        H4 = H3
        T4 = CP.PropsSI('T', 'P', low_pressure, 'H', H4, refrigerant)
        S4 = CP.PropsSI('S', 'P', low_pressure, 'H', H4, refrigerant)
        D4 = CP.PropsSI('D', 'P', low_pressure, 'H', H4, refrigerant)

        # PERFORMANCE
        compressor_work = mass_flow * (H2 - H1)
        heat_removed    = mass_flow * (H1 - H4)
        heat_rejected   = mass_flow * (H2 - H3)
        COP = heat_removed / compressor_work if compressor_work != 0 else 0.0

        # Convert to IP
        comp_btu_hr = convert_from_si("Heat", compressor_work)
        rem_btu_hr  = convert_from_si("Heat", heat_removed)
        rej_btu_hr  = convert_from_si("Heat", heat_rejected)

        tons_ref   = rem_btu_hr / 12000.0
        comp_kW    = compressor_work / 1000.0
        kw_per_ton = comp_kW / tons_ref if tons_ref > 0 else float('inf')

        # DISPLAY
        self.output_text.delete("1.0", tk.END)

        # Summarize
        self.output_text.insert(tk.END, f"Refrigerant: {refrigerant}\n")
        self.output_text.insert(tk.END, f"Reference State: {ref_state}\n")
        self.output_text.insert(tk.END, f"Evaporator Input: {evap_value} ({evap_type})\n")
        self.output_text.insert(tk.END, f"Condenser Input: {cond_value} ({cond_type})\n")
        self.output_text.insert(tk.END, f"Superheat: {superheat_F:.1f} °F\n")
        self.output_text.insert(tk.END, f"Subcooling: {subcooling_F:.1f} °F\n")
        self.output_text.insert(tk.END, f"Isentropic Efficiency: {isentropic_eff*100:.1f}%\n")
        self.output_text.insert(tk.END, f"Mass Flow Rate: {mass_flow_lb_min:.2f} lb/min\n\n")

        self.output_text.insert(tk.END, "--- Refrigeration Cycle Results (IP Units) ---\n")
        table_header = (
            " State |   T(°F)  |  P(psia)  | density(lbm/ft³) |  h(BTU/lb) |  s(BTU/lbm·°F)\n"
            "-----------------------------------------------------------------------------\n"
        )
        self.output_text.insert(tk.END, table_header)

        states = [
            (T1, low_pressure, D1, H1, S1),
            (T2, high_pressure, D2, H2, S2),
            (T3, high_pressure, D3, H3, S3),
            (T4, low_pressure, D4, H4, S4),
        ]

        for i, (temp, press, dens, enth, entr) in enumerate(states, start=1):
            T_ip = convert_from_si("T", temp)
            P_ip = convert_from_si("P", press)
            D_ip = convert_from_si("D", dens)
            H_ip = convert_from_si("H", enth)
            S_ip = convert_from_si("S", entr)
            self.output_text.insert(
                tk.END,
                f"  {i:>4d} | {T_ip:8.1f} | {P_ip:9.1f} | {D_ip:13.2f} | {H_ip:10.1f} | {S_ip:14.3f}\n"
            )

        self.output_text.insert(tk.END, "\n--- Performance Metrics (IP Units) ---\n")
        self.output_text.insert(
            tk.END,
            f"Compressor Work Input: {comp_btu_hr:,.0f} BTU/hr ({comp_kW:.1f} kW)\n"
        )
        self.output_text.insert(
            tk.END,
            f"Heat Removed (Cooling Capacity): {rem_btu_hr:,.0f} BTU/hr ({tons_ref:,.2f} Tons)\n"
        )
        self.output_text.insert(tk.END, f"Heat Rejected by Condenser: {rej_btu_hr:,.0f} BTU/hr\n")
        self.output_text.insert(tk.END, f"Coefficient of Performance (COP): {COP:.2f}\n")
        self.output_text.insert(tk.END, f"kW per Ton: {kw_per_ton:.2f}\n")

    # "About" info
    def show_info(self):
        info_text = (
            "Refrigeration Cycle Simulator\n\n"
            "This program calculates the performance of a refrigeration cycle. The user can specify operating "
            "temperatures or pressures, compressor efficiency, and mass flow rate of refrigerant. The program will "
            "output thermodynamic properties, cooling capacity, and cycle efficiency for the chosen refrigerant.\n"
            "Observe from the 1st Law of Thermo that the compressor work plus the heat absorbed in the evaporator "
            "equals the heat rejected by the condenser!\n\n"
            "Developed in Python by Alex Kalmbach"
        )
        messagebox.showinfo("About Refrigeration Cycle Simulator", info_text)

    def show_ref_state_info(self):
        ref_text = (
            "Reference State Information:\n\n"
            "ASHRAE: Often used in textbooks (Cengel, etc.)\n"
            "NBP: Normal Boiling Point reference\n"
            "IIR: International Institute of Refrigeration (used in Danfoss Coolselector2)\n\n"
            "These shift absolute enthalpy/entropy values,\n"
            "but not the relative changes."
        )
        messagebox.showinfo("Reference State Info", ref_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = RefrigerationCycleGUI(root)
    root.mainloop()
