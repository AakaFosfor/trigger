package miclockGui;

import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

import dim.DimClient;
import dim.DimInfo;

/**
 * Class that communicates with the Dim interface.
 * @author oerjan
 *
 */
public class MiClockClient
{
	
	private DimInfo miclock;
	private DimInfo beammode;
	private DimInfo clocktrans;
	private final PropertyChangeSupport pcs = new PropertyChangeSupport(this);
	
	/**
	 * Constructor
	 */
	public MiClockClient()
	{
		if (!Main.GUI_SHELL_MODE) {
			
			this.miclock = new DimInfo("TTCMI/MICLOCK", -1)
			{
				public void infoHandler()
				{
					MiClockClient.this.pcs.firePropertyChange(
							new PropertyChangeEvent(
									this, "miclock",-1, this.getString()));
				}
			};
			
			this.beammode = new DimInfo("CTPDIM/BEAMMODE", -1)
			{
				public void infoHandler()
				{
					MiClockClient.this.pcs.firePropertyChange(
							new PropertyChangeEvent(
									this, "beammode", -1, this.getInt()));
				}
			};
			
			this.clocktrans = new DimInfo("TTCMI/MICLOCK_TRANSITION", -1)
			{
				public void infoHandler()
				{
					MiClockClient.this.pcs.firePropertyChange(
							new PropertyChangeEvent(
									this, "clocktrans", -1, this.getString()));
				}
			};
			
		}
	}
	
	/**
	 * Returns the state of the miclock.
	 * @return State of miclock
	 */
	public String getMiclock()
	{
		return this.miclock.getString();
	}
	
	/**
	 * Returns the beammode as a Integer.
	 * @return Beammode as a Integer
	 */
	public int getBeammodeInt()
	{
		return this.beammode.getInt();	
	}
	
	/**
	 * Returns the beammode as a String.
	 * @return Beammode as a String
	 */
	public String getBeammodeString()
	{
		switch(this.beammode.getInt())
		{
		case 1: return "NO MODE"; 					//0 - Local
		case 2: return "SETUP";						//0 - Local
		case 3: return "INJECTION PROBE BEAM";		//0 - Local
		case 4: return "INJECTION SETUP BEAM";		//1 - BeamClock
		case 5: return "INJECTION PHYSICS BEAM";	//1 - BeamClock
		case 6: return "PREPARE RAMP";				//1 - BeamClock
		case 7: return "RAMP";						//1 - BeamClock
		case 8: return "FLAT TOP";        			//1 - BeamClock - CLOCKSHIFT VALID only in these 4 modes (PHASE_SHIFT_BPTX1 dim)
		case 9: return "SQUEEZE";					//1 - BeamClock - CLOCKSHIFT VALID
		case 10: return "ADJUST";					//1 - BeamClock - CLOCKSHIFT VALID
		case 11: return "STABLE BEAMS";				//1 - BeamClock - CLOCKSHIFT VALID
		case 12: return "UNSTABLE BEAMS";			//0 - Local
		case 13: return "BEAM DUMP";				//0 - Local
		case 14: return "RAMP DOWN";				//0 - Local
		case 15: return "RECOVERY";					//0 - Local
		case 16: return "INJECT & DUMP";			//0 - Local
		case 17: return "CIRCULATE & DUMP";			//0 - Local
		case 18: return "ABORT"; 					//0 - Local
		case 19: return "CYCLING";					//0 - Local
		case 20: return "BEAM DUMP WARNING";		//0 - Local
		case 21: return "NO BEAM";					//0 - Local
		}
		return "ERROR";
	}
	
	/**
	 * Returns the state of the clock transition.
	 * @return State of the clock transition.
	 */
	public String getClocktrans()
	{
		return this.clocktrans.getString();
	}
	
	/**
	 * Returns the shift of the clock. 
	 * @return Shift of the clock.
	 */
	public String getShift()
	{
		Runtime rt = Runtime.getRuntime();
		String shiftValue = "";
		try {
			//TODO : Find the correct placemtn of monshiftclock2.py
			Process pro = rt.exec("python /home/oerjan/ttcmidaemons/" +
					"monshiftclock2.py 1");
			BufferedReader br = new BufferedReader(
					new InputStreamReader(pro.getInputStream()));
			pro.waitFor();
			while(br.ready())
			{
				shiftValue += br.readLine();
			}
			br.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return shiftValue;
	}
	
	/**
	 * Updates all the DimInfo objects.
	 */
	public void updateAll()
	{
		this.miclock.infoHandler();
		this.clocktrans.infoHandler();
		this.beammode.infoHandler();
	}
	
	/**
	 * Releases the DimInfo objects.
	 */
	public void shutdown()
	{
		this.miclock.releaseService();
		this.beammode.releaseService();
		this.clocktrans.releaseService();
	}
	
	/**
	 * Sends a MICLOCK_SET command.
	 * @param cmd Command to be sent. (BEAM1, BEAM2, REF or LOCAL)
	 */
	public void sendMiClockSetCommand(String cmd)
	{
		DimClient.sendCommandNB("TTCMI/MICLOCK_SET", cmd);
		this.pcs.firePropertyChange(
				new PropertyChangeEvent(this, "sendClock", -1, cmd));
	}
	
	/**
	 * Sends a CORDE_SET command.
	 * @param value 
	 */
	public void sendShiftCommand(int value)
	{
		int i = DimClient.sendCommandNB("TTCMI/CORDE_SET", value);
		this.pcs.firePropertyChange(
				new PropertyChangeEvent(this, "sendShift", -1, value));
		System.out.println(i);
	}
	
	/**
	 * A method for the ButtonPanel to communicate mode changes (AUTO/MANUAL)
	 * to the InfoPanel and HTMLWriter.
	 */
	public void sendOperChange(String oper)
	{
		this.pcs.firePropertyChange(
				new PropertyChangeEvent(this, "sendOper", -1, oper));
	}
	
	/**
	 * A method for the ButtonPanel to communicate to the InfoPanel to get the
	 * shift.
	 */
	public void sendGetShift()
	{
		this.pcs.firePropertyChange(
				new PropertyChangeEvent(this, "getShift", -1, this.getShift()));
	}
	
	/**
	 * Adds a Property Change Listener to the Property Change Support object.
	 * pcs is used to communicate changes to the ButtonPanel and InfoPanel
	 */
	public void addPropertyChangeListener(PropertyChangeListener listener)
	{
		this.pcs.addPropertyChangeListener(listener);
	}
	
	/**
	 * Removes a Property Change Listener from the Property Change Support 
	 * object. This method is never used (11.07.12).
	 */
	public void removePropertyChangeListener(PropertyChangeListener listener)
	{
		this.pcs.removePropertyChangeListener(listener);
	}
	
}
